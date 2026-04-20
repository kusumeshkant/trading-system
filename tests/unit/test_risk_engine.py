import pytest
from app.risk.engine import RiskEngine, RiskContext
from app.core.exceptions import RiskLimitBreached, KillSwitchTriggered


@pytest.fixture
def risk():
    return RiskEngine()


def test_valid_trade_passes(risk):
    ctx = RiskContext(capital=20000, daily_loss=0, open_trades=1, proposed_size=1000, leverage=3)
    risk.validate(ctx)  # should not raise


def test_daily_loss_limit_triggers_kill_switch(risk):
    ctx = RiskContext(capital=20000, daily_loss=-1200, open_trades=0, proposed_size=500, leverage=1)
    with pytest.raises((RiskLimitBreached, KillSwitchTriggered)):
        risk.validate(ctx)


def test_max_open_trades_blocks(risk):
    ctx = RiskContext(capital=20000, daily_loss=0, open_trades=3, proposed_size=500, leverage=1)
    with pytest.raises(RiskLimitBreached):
        risk.validate(ctx)


def test_position_size_too_large(risk):
    ctx = RiskContext(capital=20000, daily_loss=0, open_trades=0, proposed_size=5000, leverage=1)
    with pytest.raises(RiskLimitBreached):
        risk.validate(ctx)


def test_kill_switch_blocks_all(risk):
    risk.activate_kill_switch("test")
    ctx = RiskContext(capital=20000, daily_loss=0, open_trades=0, proposed_size=100, leverage=1)
    with pytest.raises(KillSwitchTriggered):
        risk.validate(ctx)


def test_position_sizing():
    risk = RiskEngine()
    qty = risk.calculate_position_size(
        capital=20000, risk_percent=1.0, entry_price=50000, stop_loss_price=49000
    )
    assert qty == pytest.approx(0.2, rel=0.01)
