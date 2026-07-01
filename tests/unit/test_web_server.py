import http.client
import json
import threading

from app.web_server import create_server


def start_test_server():
    server = create_server("127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def stop_test_server(server, thread):
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)


def make_website_state_payload() -> dict:
    return {
        "table_id": "real-table-1",
        "hand_id": "real-hand-001",
        "street": "flop",
        "position": "BTN_vs_BB",
        "current_actor": "hero",
        "hero_cards": ["Ah", "Kh"],
        "board_cards": ["Kc", "8d", "3s"],
        "pot": 100,
        "stacks": {
            "hero": 900,
            "villain": 900,
        },
        "facing_action": {
            "player": "BB",
            "action": "check",
            "size": 0,
        },
    }


def test_server_serves_index_page():
    server, thread = start_test_server()
    host, port = server.server_address

    try:
      connection = http.client.HTTPConnection(host, port, timeout=5)
      connection.request("GET", "/")
      response = connection.getresponse()
      body = response.read().decode("utf-8")
    finally:
      stop_test_server(server, thread)

    assert response.status == 200
    assert response.getheader("Content-Type") == "text/html; charset=utf-8"
    assert "德州扑克 LBS-Lite 测试面板" in body


def test_server_analyze_endpoint_returns_strategy_json():
    server, thread = start_test_server()
    host, port = server.server_address
    payload = {
        "mode": "single",
        "table_size": 2,
        "street": "flop",
        "position": "BTN_vs_BB",
        "current_actor": "hero",
        "hero_seat": "hero",
        "known_hands": {"hero": ["Ah", "Kh"]},
        "unknown_seats": ["villain"],
        "board": ["Kc", "8d", "3s"],
        "pot": 100,
        "effective_stacks": {"hero": 900, "villain": 900},
        "action_history": [{"player": "BB", "action": "check"}],
        "objective": "actor_ev",
    }

    try:
      connection = http.client.HTTPConnection(host, port, timeout=5)
      connection.request(
          "POST",
          "/api/analyze",
          body=json.dumps(payload).encode("utf-8"),
          headers={"Content-Type": "application/json"},
      )
      response = connection.getresponse()
      body = json.loads(response.read().decode("utf-8"))
    finally:
      stop_test_server(server, thread)

    assert response.status == 200
    assert body["ok"] is True
    assert body["result"]["recommend"] in body["result"]["strategy"]


def test_server_import_website_state_endpoint_returns_converted_raw_state():
    server, thread = start_test_server()
    host, port = server.server_address
    payload = make_website_state_payload()

    try:
      connection = http.client.HTTPConnection(host, port, timeout=5)
      connection.request(
          "POST",
          "/api/import-website-state",
          body=json.dumps(payload).encode("utf-8"),
          headers={"Content-Type": "application/json"},
      )
      response = connection.getresponse()
      body = json.loads(response.read().decode("utf-8"))
    finally:
      stop_test_server(server, thread)

    assert response.status == 200
    assert body["ok"] is True
    assert body["collected_state"]["hand_id"] == "real-hand-001"
    assert body["raw_state"]["known_hands"] == {"hero": ["Ah", "Kh"]}
    assert body["raw_state"]["action_history"] == [
        {"player": "BB", "action": "check"}
    ]


def test_server_returns_400_for_invalid_json():
    server, thread = start_test_server()
    host, port = server.server_address

    try:
      connection = http.client.HTTPConnection(host, port, timeout=5)
      connection.request(
          "POST",
          "/api/analyze",
          body=b"{not-json",
          headers={"Content-Type": "application/json"},
      )
      response = connection.getresponse()
      body = json.loads(response.read().decode("utf-8"))
    finally:
      stop_test_server(server, thread)

    assert response.status == 400
    assert body == {"ok": False, "error": "INVALID_JSON"}


def test_server_import_website_state_returns_400_for_invalid_json():
    server, thread = start_test_server()
    host, port = server.server_address

    try:
      connection = http.client.HTTPConnection(host, port, timeout=5)
      connection.request(
          "POST",
          "/api/import-website-state",
          body=b"{not-json",
          headers={"Content-Type": "application/json"},
      )
      response = connection.getresponse()
      body = json.loads(response.read().decode("utf-8"))
    finally:
      stop_test_server(server, thread)

    assert response.status == 400
    assert body == {"ok": False, "error": "INVALID_JSON"}


def test_server_returns_400_for_invalid_utf8_json_body():
    server, thread = start_test_server()
    host, port = server.server_address

    try:
      connection = http.client.HTTPConnection(host, port, timeout=5)
      connection.request(
          "POST",
          "/api/analyze",
          body=b"\xff",
          headers={"Content-Type": "application/json"},
      )
      response = connection.getresponse()
      body = json.loads(response.read().decode("utf-8"))
    finally:
      stop_test_server(server, thread)

    assert response.status == 400
    assert body == {"ok": False, "error": "INVALID_JSON"}


def test_server_returns_400_for_malformed_state_shape():
    server, thread = start_test_server()
    host, port = server.server_address
    payload = {
        "mode": "single",
        "table_size": 2,
        "street": "flop",
        "position": "BTN_vs_BB",
        "current_actor": "hero",
        "hero_seat": "hero",
        "known_hands": [],
        "unknown_seats": ["villain"],
        "board": ["Kc", "8d", "3s"],
        "pot": 100,
        "effective_stacks": {"hero": 900, "villain": 900},
        "action_history": [{"player": "BB", "action": "check"}],
        "objective": "actor_ev",
    }

    try:
      connection = http.client.HTTPConnection(host, port, timeout=5)
      connection.request(
          "POST",
          "/api/analyze",
          body=json.dumps(payload).encode("utf-8"),
          headers={"Content-Type": "application/json"},
      )
      response = connection.getresponse()
      body = json.loads(response.read().decode("utf-8"))
    finally:
      stop_test_server(server, thread)

    assert response.status == 400
    assert body["ok"] is False
    assert body["error"]


def test_server_import_website_state_returns_400_for_malformed_collected_state():
    server, thread = start_test_server()
    host, port = server.server_address
    payload = make_website_state_payload()
    del payload["hero_cards"]

    try:
      connection = http.client.HTTPConnection(host, port, timeout=5)
      connection.request(
          "POST",
          "/api/import-website-state",
          body=json.dumps(payload).encode("utf-8"),
          headers={"Content-Type": "application/json"},
      )
      response = connection.getresponse()
      body = json.loads(response.read().decode("utf-8"))
    finally:
      stop_test_server(server, thread)

    assert response.status == 400
    assert body == {"ok": False, "error": "INVALID_COLLECTED_STATE: hero_cards"}


def test_server_collected_state_endpoint_returns_sample_raw_state():
    server, thread = start_test_server()
    host, port = server.server_address

    try:
      connection = http.client.HTTPConnection(host, port, timeout=5)
      connection.request("GET", "/api/collected-state?scenario=bet")
      response = connection.getresponse()
      body = json.loads(response.read().decode("utf-8"))
    finally:
      stop_test_server(server, thread)

    assert response.status == 200
    assert body["ok"] is True
    assert body["collected_state"]["hand_id"] == "demo-bet-001"
    assert body["raw_state"]["action_history"] == [
        {"player": "BB", "action": "bet", "size": 50}
    ]


def test_server_collected_state_endpoint_returns_400_for_unknown_scenario():
    server, thread = start_test_server()
    host, port = server.server_address

    try:
      connection = http.client.HTTPConnection(host, port, timeout=5)
      connection.request("GET", "/api/collected-state?scenario=unknown")
      response = connection.getresponse()
      body = json.loads(response.read().decode("utf-8"))
    finally:
      stop_test_server(server, thread)

    assert response.status == 400
    assert body == {
        "ok": False,
        "error": "UNSUPPORTED_COLLECTED_SCENARIO",
    }
