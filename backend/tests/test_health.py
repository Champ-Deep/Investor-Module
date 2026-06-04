from cadence.server import create_app


def test_health_route_registered():
    app = create_app()
    paths = {route.path for route in app.routes}
    assert "/api/health" in paths
