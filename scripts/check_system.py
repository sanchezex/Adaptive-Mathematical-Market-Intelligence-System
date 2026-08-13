#!/usr/bin/env python3
"""Run lightweight runtime checks for AMMIS components.

Usage: activate venv and run `python3 scripts/check_system.py`.
"""
import importlib, traceback, sys

checks = [
    ('models.probabilities', 'ammis.models.probabilities', "import and instantiate ModelVote"),
    ('aggregator', 'ammis.engines.market_math.aggregator', "call aggregate_votes with sample votes"),
    ('risk', 'ammis.risk.engine', "instantiate RiskEngine and call approve/record_loss"),
    ('execution', 'ammis.execution.broker', "instantiate ExecutionEngine and submit Order"),
    ('kronos_adapter', 'ammis.engines.kronos_adapter', "instantiate KronosAdapter(use_mock=True) and load()"),
    ('backtester', 'ammis.backtest.backtester', "instantiate SimpleBacktester with mock adapter"),
    ('db', 'ammis.core.db', "connect() and show in-memory client"),
    ('migrations', 'ammis.core.db_migrate', "import run_migrations (no execute)")
]

results = []
for name, modpath, desc in checks:
    try:
        mod = importlib.import_module(modpath)
        ok = True
        note = ''
        # do light exercises
        if name=='models.probabilities':
            cls = getattr(mod,'ModelVote')
            mv = cls(model='t', action='BUY', confidence=50.0)
            note = repr(mv.dict())
        elif name=='aggregator':
            mvcls = importlib.import_module('ammis.models.probabilities').ModelVote
            v = mvcls(model='m', action='BUY', confidence=70)
            res = mod.aggregate_votes([v], threshold=10.0)
            note = f"overall={res.overall_action}, conf={res.overall_confidence}"
        elif name=='risk':
            cls = getattr(mod,'RiskEngine')
            r = cls()
            a = r.approve('BUY', expected_loss=1.0)
            r.record_loss(5.0)
            note = f"approve_before={a}, daily_loss={r.current_daily_loss}"
        elif name=='execution':
            Order = getattr(mod,'Order')
            Exec = getattr(mod,'ExecutionEngine')
            exe = Exec()
            o = Order(action='BUY', symbol='X', quantity=1)
            fill = exe.submit(o)
            note = f"fill_status={fill.get('status')}"
        elif name=='kronos_adapter':
            KronosAdapter = getattr(mod,'KronosAdapter')
            ka = KronosAdapter(use_mock=True)
            ka.load()
            note = f"available={ka.available()}"
        elif name=='backtester':
            cls = getattr(mod,'SimpleBacktester')
            # construct with mock adapter
            ka = importlib.import_module('ammis.engines.kronos_adapter').KronosAdapter(use_mock=True)
            ka.load()
            bt = cls(adapter=ka)
            note = 'created'
        elif name=='db':
            okconn = mod.connect()
            note = f"connected={okconn}, in_memory_keys={list(mod._db_client.in_memory.keys())}"
        elif name=='migrations':
            # just import
            note = 'imported'
        results.append((name, True, note))
    except Exception as e:
        tb = traceback.format_exc()
        results.append((name, False, tb.splitlines()[-1]))

print('CHECK SUMMARY')
failed = False
for name, ok, note in results:
    print(f"- {name}: {'OK' if ok else 'FAIL'} - {note}")
    if not ok:
        failed = True

if failed:
    sys.exit(2)
