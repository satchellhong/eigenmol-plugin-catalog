#!/usr/bin/env python3
"""Atom counts: the EigenMol plugin starter template.

Everything here follows docs/plugins/PLUGIN_SPECIFICATION.md and nothing else.
Copy the folder, rename the id, and replace `count_atoms` with a call to your
own program. Standard library only.

The four parts every plugin has:

1. the transport: Content-Length framed JSON on stdin/stdout (spec §6),
2. the handshake: answer at once with the actions you serve (spec §7),
3. invoke: read the input snapshot (spec §8), compute, return typed results
   (spec §9), or a typed error (spec §11),
4. the check: one JSON readiness report on stdout (spec §12).

stdout carries protocol messages only. Log to stderr.
"""
import collections
import json
import sys

PROTOCOL = 1
PLUGIN_ID = "org.example.atomcounts"
PLUGIN_VERSION = "0.1.0"


def log(text):
    print(f"[atomcounts] {text}", file=sys.stderr, flush=True)


# --- 1. transport ----------------------------------------------------------

def read_message():
    length = None
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None  # EigenMol closed stdin: exit
        text = line.decode("utf-8", "replace").strip()
        if not text:
            break  # blank line ends the headers
        name, _, value = text.partition(":")
        if name.strip().lower() == "content-length":
            length = int(value.strip())
    if length is None:
        return None
    return json.loads(sys.stdin.buffer.read(length).decode("utf-8"))


def write_message(message):
    body = json.dumps(message).encode("utf-8")
    sys.stdout.buffer.write(b"Content-Length: %d\r\n\r\n" % len(body))
    sys.stdout.buffer.write(body)
    sys.stdout.buffer.flush()


def respond(request_id, result):
    write_message({"protocol": PROTOCOL, "kind": "response", "id": request_id, "result": result})


def refuse(request_id, code, message, detail=None):
    error = {"code": code, "message": message}
    if detail:
        error["detail"] = detail
    write_message({"protocol": PROTOCOL, "kind": "response", "id": request_id, "error": error})


class Refusal(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code, self.message = code, message


# --- 3. the computation ----------------------------------------------------

def count_atoms(inputs):
    """Atoms by element and by chain, from the structure snapshot (spec §8)."""
    atoms = inputs.get("atoms") or []
    if not atoms:
        raise Refusal("invalid_input", "The structure has no atoms to count.")
    object_handle = inputs["identity"]["object"]
    by_element = collections.Counter(atom["element"] for atom in atoms)
    by_chain = collections.Counter(atom["chain"] for atom in atoms)
    count_quantity = {"key": "org.example.atomcounts.atom_count", "label": "Atom count"}
    table = {
        "type": "table",
        "name": "Atoms by element",
        "provenance": {"method": "counting the atoms EigenMol sent, by element"},
        "columns": [
            {"name": "Element", "kind": "text"},
            {"name": "Atoms", "kind": "number", "unit": "unitless", "quantity": count_quantity},
        ],
        "rows": [{"cells": [element, count]} for element, count in sorted(by_element.items())],
    }
    metadata = {
        "type": "metadata",
        "name": "Atoms by chain",
        "provenance": {"method": "counting the atoms EigenMol sent, by chain"},
        "entries": [
            {"key": f"chain {chain or '(blank)'}", "value": count}
            for chain, count in sorted(by_chain.items())
        ] + [{"key": "object", "value": object_handle}],
    }
    return [table, metadata]


ACTIONS = {"count_atoms": count_atoms}


# --- 4. the check ----------------------------------------------------------

def check():
    ok = sys.version_info >= (3, 8)
    print(json.dumps({
        "ready": ok,
        "summary": "Atom counts is ready." if ok else "Python 3.8 or newer is needed.",
        "items": [{
            "name": "Python",
            "status": "ok" if ok else "error",
            "detail": sys.version.split()[0],
            "fix": "" if ok else "Install Python 3.8 or newer.",
        }],
    }))
    return 0


# --- 2. the conversation ---------------------------------------------------

def main():
    if "--check" in sys.argv[1:]:
        return check()
    while True:
        message = read_message()
        if message is None:
            return 0
        if message.get("kind") != "request":
            continue
        request_id, method = message.get("id"), message.get("method")
        if method == "handshake":
            respond(request_id, {
                "protocol": PROTOCOL,
                "sdk": f"{PLUGIN_ID}/{PLUGIN_VERSION}",
                "actions": sorted(ACTIONS),
                "concurrent_requests": 1,
            })
        elif method == "invoke":
            params = message.get("params") or {}
            handler = ACTIONS.get(params.get("action"))
            if handler is None:
                refuse(request_id, "unsupported_action", f"no action {params.get('action')!r}")
                continue
            try:
                respond(request_id, {"results": handler(params.get("inputs") or {})})
            except Refusal as refusal:
                refuse(request_id, refusal.code, refusal.message)
            except Exception as error:  # noqa: BLE001 - the user reads a sentence
                log(f"failed: {error!r}")
                refuse(request_id, "calculation_failed", "Atom counts failed.", repr(error))
        elif method == "cancel":
            return 0


if __name__ == "__main__":
    sys.exit(main())
