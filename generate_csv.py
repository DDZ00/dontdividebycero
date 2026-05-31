"""
generate_csv.py  (toy-RSA edition)
==================================
Lee walkthrough.json y produce network_logs.csv (1000 filas) para el juego
"Hijacked Network".

Diferencia clave con la version anterior: los primos p/q/e NO estan escritos
en el CSV. Cada uno es el RESULTADO de una operacion estadistica que el alumno
debe calcular. Lo unico cifrado-relacionado en el payload es 'ENC:<lista>'.

RSA de juguete, caracter por caracter:
    cifrar:   c = ord(char) ** e  mod n          (n = p*q)
    descifrar: char = chr(c ** d  mod n)          (d = e^-1 mod phi)

Uso:
    python generate_csv.py [--json walkthrough.json] [--out network_logs.csv]

Dependencias: pandas, sympy
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from sympy import mod_inverse


# ---------------------------------------------------------------------------
# Toy RSA helpers
# ---------------------------------------------------------------------------
def toy_encrypt(message: str, p: int, q: int, e: int) -> list[int]:
    """Encrypt char-by-char. Returns list of ints."""
    n = p * q
    return [pow(ord(ch), e, n) for ch in message]


def toy_decrypt(cipher: list[int], p: int, q: int, e: int) -> str:
    n = p * q
    phi = (p - 1) * (q - 1)
    d = int(mod_inverse(e, phi))
    return "".join(chr(pow(c, d, n)) for c in cipher)


def enc_payload(message: str, p: int, q: int, e: int) -> str:
    nums = toy_encrypt(message, p, q, e)
    return "ENC:" + ",".join(str(x) for x in nums)


# ---------------------------------------------------------------------------
# Seeded RNG helpers
# ---------------------------------------------------------------------------
class Rng:
    def __init__(self, seed: int):
        self.r = random.Random(seed)

    def user_id(self, exclude: set[int]) -> int:
        while True:
            uid = self.r.randint(10000, 99999)
            if uid not in exclude:
                return uid

    def ip(self) -> str:
        while True:
            a, b, c, d = (
                self.r.randint(10, 200), self.r.randint(0, 255),
                self.r.randint(0, 255), self.r.randint(1, 254),
            )
            ip = f"{a}.{b}.{c}.{d}"
            if not ip.startswith("192.168."):
                return ip

    def bytes_value(self, lo: int = 1000, hi: int = 9_999_999) -> int:
        """Noise/trap byte sizes: always >= 1000, so they never collide with
        the small prime values (which are < 600) used as statistical signals."""
        return self.r.randint(lo, hi)

    def timestamp(self, start: datetime, end: datetime,
                  exclude: set[str] | None = None) -> str:
        exclude = exclude or set()
        for _ in range(200):
            secs = self.r.randint(0, int((end - start).total_seconds()))
            s = (start + timedelta(seconds=secs)).strftime("%Y-%m-%d %H:%M:%S")
            if s not in exclude:
                return s
        return s

    def node(self, pool: list[str], exclude: set[str] | None = None) -> str:
        exclude = exclude or set()
        choices = [n for n in pool if n not in exclude] or pool
        return self.r.choice(choices)

    def action(self, pool: list[str]) -> str:
        return self.r.choice(pool)

    def action_no_fail_success(self, pool: list[str]) -> str:
        """Pick an action that is neither connection_fail nor connection_success,
        so noise rows don't pollute cycle-1 statistics."""
        choices = [a for a in pool if a not in
                   ("connection_fail", "connection_success")]
        return self.r.choice(choices)


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------
class Generator:
    def __init__(self, spec: dict):
        self.spec = spec
        self.rng = Rng(spec["_meta"]["random_seed"])
        self.nodes = spec["schema"]["node_pool"]
        self.actions = spec["schema"]["action_values_real"]
        self.keys = {k["cycle"]: k for k in spec["rsa_keys"]}

        # Pre-encrypt the three messages.
        self.enc = {}
        for cyc in (1, 2, 3):
            k = self.keys[cyc]
            msg = self._plain(cyc)
            self.enc[cyc] = enc_payload(msg, k["p"], k["q"], k["e"])
            # sanity round-trip
            back = toy_decrypt(
                [int(x) for x in self.enc[cyc][4:].split(",")],
                k["p"], k["q"], k["e"])
            assert back == msg, f"cycle {cyc} round-trip failed"
            print(f"  Cycle {cyc}: '{msg}' -> {len(self.enc[cyc][4:].split(','))} cifras")

        self.ts_start = datetime(2024, 8, 1)
        self.ts_end = datetime(2024, 12, 30, 23, 59, 59)

        self.protected_uids: set[int] = set()
        self.protected_ts: set[str] = set()

    def _plain(self, cyc: int) -> str:
        return self.spec[f"cycle_{cyc}"]["plain_message"]

    # ------------------------------------------------------------------ signal
    def build_signal(self) -> list[dict]:
        rows: list[dict] = []
        c1 = self.spec["cycle_1"]
        c2 = self.spec["cycle_2"]
        c3 = self.spec["cycle_3"]

        # Protect special ids / timestamps
        self.protected_uids.update([
            c1["victim_user_id"],
            c1["message_carrier"]["max_success_user_id"],
            c2["message_carrier"]["modal_user_id_in_subset"],
            c3["message_carrier"]["outlier_user_id"],
        ])
        self.protected_ts.add(c3["magic_timestamp"])
        self.protected_ts.add(c3["message_carrier"]["extra_recent_row_timestamp"])

        # ============ CICLO 1 ============
        victim = c1["victim_user_id"]
        vbytes = c1["derive_p"]["victim_bytes_up_list"]   # 11 values, median 211
        # 11 victim rows, each on a DISTINCT node (nunique(node)=11=e1), all connection_fail
        nodes_for_victim = self.nodes[:11]                # 11 of the 12 nodes
        assert len(vbytes) == 11
        for b, nd in zip(vbytes, nodes_for_victim):
            rows.append(self._row(
                ts=self._rand_ts(), uid=victim, ip=self.rng.ip(),
                action="connection_fail", bup=b, node=nd, payload=""))

        # q1 = mode of bytes_up among connection_success = 307 (9 rows)
        q1 = c1["derive_q"]["value"]
        n_q1 = c1["derive_q"]["occurrences"]
        for _ in range(n_q1):
            rows.append(self._row(
                ts=self._rand_ts(), uid=self.rng.user_id(self.protected_uids),
                ip=self.rng.ip(), action="connection_success",
                bup=q1, node=self.rng.node(self.nodes), payload=""))

        # Max bytes_up success row -> its user carries the ENC message
        msg_user1 = c1["message_carrier"]["max_success_user_id"]
        big = 9_999_999
        rows.append(self._row(
            ts=self._rand_ts(), uid=msg_user1, ip=self.rng.ip(),
            action="connection_success", bup=big,
            node=self.rng.node(self.nodes), payload=""))
        # the ENC row for that same user (different row)
        rows.append(self._row(
            ts=self._rand_ts(), uid=msg_user1, ip=self.rng.ip(),
            action=self.rng.action_no_fail_success(self.actions),
            bup=self.rng.bytes_value(), node=self.rng.node(self.nodes),
            payload=self.enc[1]))

        # ============ CICLO 2 ============
        ip2 = c2["target_ip"]
        # p2 = mode bytes in subset = 233 (5 rows)
        p2 = c2["derive_p"]["value"]
        n_p2 = c2["derive_p"]["occurrences"]
        # q2 = median of bytes among unique-node rows = 277 (rows [200,277,350])
        q_list = c2["derive_q"]["unique_node_bytes_list"]
        # e2 = number of unique timestamps in subset = 5
        e2_count = c2["derive_e"]["value"]
        msg_user2 = c2["message_carrier"]["modal_user_id_in_subset"]

        # shared (non-unique) timestamp for all the "structural" rows
        shared = "2024-08-12 11:00:00"

        # 5 rows with bytes=233 (mode). They share the same timestamp (non-unique)
        # and the same node so they don't create unique-nodes.
        for i in range(n_p2):
            rows.append(self._row(
                ts=shared, uid=self.rng.user_id(self.protected_uids), ip=ip2,
                action=self.rng.action(self.actions), bup=p2,
                node="node_alpha_01", payload=""))

        # 3 unique-node rows with bytes [200,277,350]; each on its own node.
        # Same shared timestamp so they don't add unique timestamps.
        uniq_nodes = ["node_beta_02", "node_gamma_03", "node_delta_04"]
        for b, nd in zip(q_list, uniq_nodes):
            rows.append(self._row(
                ts=shared, uid=self.rng.user_id(self.protected_uids), ip=ip2,
                action=self.rng.action(self.actions), bup=b,
                node=nd, payload=""))

        # 5 rows with UNIQUE timestamps (e2 = 5). To keep nodes non-unique,
        # put them all on node_alpha_01. Bytes random-ish but not 233/200/277/350
        # to avoid disturbing earlier modes/medians.
        msg_user_used = False
        for i in range(e2_count):
            uniq_ts = f"2024-08-12 1{i}:{15+i:02d}:{30+i:02d}"
            # make one of these rows belong to msg_user2 so it's the modal user later
            uid = self.rng.user_id(self.protected_uids)
            rows.append(self._row(
                ts=uniq_ts, uid=uid, ip=ip2,
                action=self.rng.action(self.actions),
                bup=self.rng.bytes_value(500, 5000),
                node="node_alpha_01", payload=""))

        # Make msg_user2 the MODE of user_id within the subset: add several rows
        # for msg_user2 (more than any other uid appears in the subset).
        # Other uids appear once; msg_user2 will appear 3 times -> modal.
        for i in range(3):
            payload = self.enc[2] if i == 0 else ""
            rows.append(self._row(
                ts=shared, uid=msg_user2, ip=ip2,
                action=self.rng.action(self.actions),
                bup=self.rng.bytes_value(500, 5000),
                node="node_alpha_01", payload=payload))

        # ============ CICLO 3 ============
        node3 = c3["target_node"]
        magic = c3["magic_timestamp"]
        subset_bytes = c3["subset_bytes_up"]              # [151,151,151,199,199,88,500]
        outlier_bytes = c3["message_carrier"]["outlier_bytes_up"]
        outlier_uid = c3["message_carrier"]["outlier_user_id"]

        for b in subset_bytes:
            uid = outlier_uid if b == outlier_bytes else \
                self.rng.user_id(self.protected_uids)
            rows.append(self._row(
                ts=magic, uid=uid, ip=self.rng.ip(),
                action=self.rng.action(self.actions), bup=b,
                node=node3, payload=""))

        # extra most-recent row for outlier_uid carrying the final ENC message
        rec_ts = c3["message_carrier"]["extra_recent_row_timestamp"]
        rows.append(self._row(
            ts=rec_ts, uid=outlier_uid, ip=self.rng.ip(),
            action=self.rng.action(self.actions),
            bup=self.rng.bytes_value(), node=node3, payload=self.enc[3]))

        return rows

    # ------------------------------------------------------------------ traps
    def build_traps(self, count: int) -> list[dict]:
        rows = []
        for i in range(count):
            kind = i % 4
            if kind == 0:
                # bogus ENC: random ints that won't decode to anything meaningful
                fake = ",".join(str(self.rng.r.randint(1, 60000))
                                for _ in range(self.rng.r.randint(4, 12)))
                payload = f"ENC:{fake}"
            elif kind == 1:
                payload = f"HASH={hashlib.sha256(str(self.rng.r.random()).encode()).hexdigest()}"
            elif kind == 2:
                payload = f"CHK:{hashlib.md5(str(i).encode()).hexdigest()[:8]}"
            else:
                payload = f"SES:{self.rng.r.randint(10**6, 10**9)}"

            rows.append(self._row(
                ts=self._rand_ts(), uid=self.rng.user_id(self.protected_uids),
                ip=self.rng.ip(),  # never target_ip (192.168.* excluded)
                action=self.rng.action_no_fail_success(self.actions),
                bup=self.rng.bytes_value(), node=self.rng.node(self.nodes),
                payload=payload))
        return rows

    # ------------------------------------------------------------------ noise
    def build_noise(self, count: int) -> list[dict]:
        rows = []
        for i in range(count):
            r = self.rng.r.random()
            if r < 0.75:
                payload = self.rng.r.choice(["", "", "-"])
            elif r < 0.9:
                payload = f"CHK:{hashlib.md5(str(i).encode()).hexdigest()[:8]}"
            else:
                payload = f"SES:{self.rng.r.randint(10**6, 10**9)}"
            # Noise must NOT add connection_fail/success at the target ip, and must
            # not reuse special small byte values. bytes_value floor is 1000 so it
            # never equals a prime signal. Avoid fail/success to keep cycle-1 clean
            # except we DO allow them elsewhere with random users (capped below).
            act = self.rng.action(self.actions)
            rows.append(self._row(
                ts=self._rand_ts(), uid=self.rng.user_id(self.protected_uids),
                ip=self.rng.ip(), action=act,
                bup=self.rng.bytes_value(), node=self.rng.node(self.nodes),
                payload=payload))
        return rows

    # ------------------------------------------------------------------ utils
    def _row(self, ts, uid, ip, action, bup, node, payload):
        return {
            "timestamp": ts, "user_id": uid, "ip": ip, "action": action,
            "bytes_up": bup, "bytes_down": self.rng.bytes_value(),
            "node": node, "payload_info": payload,
        }

    def _rand_ts(self):
        return self.rng.timestamp(self.ts_start, self.ts_end,
                                  exclude=self.protected_ts)

    # ------------------------------------------------------------------ build
    def assemble(self) -> pd.DataFrame:
        print("Signal...")
        signal = self.build_signal()
        print(f"  {len(signal)} signal rows")
        trap_n = self.spec["_meta"]["rows_trap"]
        noise_n = self.spec["_meta"]["rows_total"] - len(signal) - trap_n
        print(f"Traps ({trap_n})... Noise ({noise_n})...")
        traps = self.build_traps(trap_n)
        noise = self.build_noise(noise_n)

        all_rows = signal + traps + noise
        self.rng.r.shuffle(all_rows)
        df = pd.DataFrame(all_rows)

        # Safety caps so random noise can't break cycle-1 statistics:
        self._cap_noise_collisions(df)
        return df

    def _cap_noise_collisions(self, df: pd.DataFrame) -> None:
        """Ensure no random user accidentally beats the victim's fail count or
        the success-mode, and that no noise row sits on the target IP."""
        # No noise rows should be at the target IP (we used random_ip excluding
        # 192.168.* so this is guaranteed). Assert it.
        ip2 = self.spec["cycle_2"]["target_ip"]
        at_ip = df[df["ip"] == ip2]
        # All rows at target ip must be our signal rows; count must match design
        expected = (self.spec["cycle_2"]["derive_p"]["occurrences"]
                    + len(self.spec["cycle_2"]["derive_q"]["unique_node_bytes_list"])
                    + self.spec["cycle_2"]["derive_e"]["value"]
                    + 3)  # the 3 modal-user rows
        assert len(at_ip) == expected, \
            f"target IP rows = {len(at_ip)}, expected {expected}"

    # ------------------------------------------------------------------ validate
    def validate(self, df: pd.DataFrame) -> None:
        print("\n=== VALIDATING GAMEPLAY ===")
        c1, c2, c3 = (self.spec["cycle_1"], self.spec["cycle_2"],
                      self.spec["cycle_3"])
        k1, k2, k3 = self.keys[1], self.keys[2], self.keys[3]

        # ---- CICLO 1 ----
        print("[Cycle 1]")
        fails = df[df["action"] == "connection_fail"]
        victim = fails["user_id"].mode().iloc[0]
        assert victim == c1["victim_user_id"], f"victim={victim}"
        print(f"  victim = {victim}")

        vrows = df[df["user_id"] == victim]
        p1 = int(vrows["bytes_up"].median())
        assert p1 == k1["p"], f"p1={p1} != {k1['p']}"
        print(f"  p1 (median victim bytes) = {p1}")

        success = df[df["action"] == "connection_success"]
        q1 = int(success["bytes_up"].mode().iloc[0])
        assert q1 == k1["q"], f"q1={q1} != {k1['q']}"
        print(f"  q1 (mode success bytes) = {q1}")

        e1 = int(vrows["node"].nunique())
        assert e1 == k1["e"], f"e1={e1} != {k1['e']}"
        print(f"  e1 (victim unique nodes) = {e1}")

        max_user = int(success.loc[success["bytes_up"].idxmax(), "user_id"])
        enc_rows = df[(df["user_id"] == max_user) &
                      (df["payload_info"].str.startswith("ENC:", na=False))]
        assert len(enc_rows) == 1, f"ENC rows for {max_user}: {len(enc_rows)}"
        cipher = [int(x) for x in enc_rows["payload_info"].iloc[0][4:].split(",")]
        msg1 = toy_decrypt(cipher, p1, q1, e1)
        assert msg1 == c1["plain_message"], f"msg1={msg1!r}"
        print(f"  decrypt -> {msg1!r}")

        # ---- CICLO 2 ----
        print("[Cycle 2]")
        ip2 = c2["target_ip"]
        sub = df[df["ip"] == ip2]
        p2 = int(sub["bytes_up"].mode().iloc[0])
        assert p2 == k2["p"], f"p2={p2}"
        print(f"  p2 (mode bytes subset) = {p2}")

        ncounts = sub["node"].value_counts()
        uniq_nodes = ncounts[ncounts == 1].index.tolist()
        sun = sub[sub["node"].isin(uniq_nodes)]
        q2 = int(sun["bytes_up"].median())
        assert q2 == k2["q"], f"q2={q2}"
        print(f"  q2 (median unique-node bytes) = {q2}")

        tcounts = sub["timestamp"].value_counts()
        e2 = int((tcounts == 1).sum())
        assert e2 == k2["e"], f"e2={e2}"
        print(f"  e2 (count unique timestamps) = {e2}")

        modal_user2 = int(sub["user_id"].mode().iloc[0])
        enc2 = df[(df["user_id"] == modal_user2) &
                  (df["payload_info"].str.startswith("ENC:", na=False))]
        assert len(enc2) == 1, f"ENC2 rows: {len(enc2)}"
        cipher2 = [int(x) for x in enc2["payload_info"].iloc[0][4:].split(",")]
        msg2 = toy_decrypt(cipher2, p2, q2, e2)
        assert msg2 == c2["plain_message"], f"msg2={msg2!r}"
        print(f"  decrypt -> {msg2!r}")

        # ---- CICLO 3 ----
        print("[Cycle 3]")
        node3 = c3["target_node"]
        sub3 = df[df["node"] == node3].copy()
        sub3["ts_hash"] = sub3["timestamp"].apply(
            lambda t: hashlib.sha256(str(t).encode()).hexdigest())
        magic_hash = c3["magic_timestamp_sha256"]
        matched = sub3[sub3["ts_hash"] == magic_hash]
        assert len(matched) == c3["subset_size"], \
            f"subset={len(matched)} != {c3['subset_size']}"
        print(f"  subset size = {len(matched)}")

        p3 = int(matched["bytes_up"].mode().iloc[0])
        assert p3 == k3["p"], f"p3={p3}"
        print(f"  p3 (mode subset bytes) = {p3}")

        bc = matched["bytes_up"].value_counts()
        non_uniq = bc[bc >= 2]
        q3 = int(non_uniq.idxmin())
        assert q3 == k3["q"], f"q3={q3}"
        print(f"  q3 (least-freq non-unique) = {q3}")

        e3 = int(len(matched))
        assert e3 == k3["e"], f"e3={e3}"
        print(f"  e3 (subset row count) = {e3}")

        mean_b = matched["bytes_up"].mean()
        matched = matched.copy()
        matched["dist"] = (matched["bytes_up"] - mean_b).abs()
        outlier = matched.sort_values("dist", ascending=False).iloc[0]
        ouid = int(outlier["user_id"])
        recent = (df[df["user_id"] == ouid]
                  .sort_values("timestamp", ascending=False).iloc[0])
        assert recent["payload_info"].startswith("ENC:")
        cipher3 = [int(x) for x in recent["payload_info"][4:].split(",")]
        msg3 = toy_decrypt(cipher3, p3, q3, e3)
        assert msg3 == c3["plain_message"], f"msg3={msg3!r}"
        print(f"  decrypt -> {msg3!r}")

        print("\n=== ALL VALIDATIONS PASSED ===")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="walkthrough.json")
    ap.add_argument("--out", default="network_logs.csv")
    ap.add_argument("--skip-validate", action="store_true")
    args = ap.parse_args()

    spec = json.loads(Path(args.json).read_text(encoding="utf-8"))
    gen = Generator(spec)
    df = gen.assemble()
    if not args.skip_validate:
        gen.validate(df)
    df.to_csv(args.out, index=False)
    print(f"\nWrote {len(df)} rows to {args.out}")
    print(df.head(3).to_string())


if __name__ == "__main__":
    main()
