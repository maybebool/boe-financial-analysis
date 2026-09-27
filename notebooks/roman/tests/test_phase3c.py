import phase3c_counterparts as p3c


def test_splitter_keeps_decimals():
    s = p3c.split_sentences("We issued USD 3.5bn. The ratio was 14.3% in 2024. NII was $91.5 billion.")
    assert s == ["We issued USD 3.5bn.", "The ratio was 14.3% in 2024.", "NII was $91.5 billion."]


def test_tolerance_examples():
    q = lambda t: p3c.quantities_precise(t)[0]
    assert p3c.matches(q("13 billion"), q("USD 13.4bn"))
    assert not p3c.matches(q("13 billion"), q("USD 13.6bn"))
    assert p3c.matches(q("1.5 billion"), q("USD 1.46bn"))
    assert p3c.matches(q("14%"), q("14.3%"))
    assert p3c.matches(q("500 million"), q("USD 0.5bn"))
    assert not p3c.matches(q("14%"), q("14 basis points"))
    assert not p3c.matches(q("1.5 billion"), q("USD 1.46bn"), exact=True)


def test_windows():
    assert p3c.window("UBS", "2024-Q1", "earnings", "W0") == ["2024-Q1"]
    w1 = p3c.window("UBS", "2024-Q1", "earnings", "W1")
    assert "2024 annual report" in w1 and all(x <= "2024-Q1" for x in w1 if "annual" not in x)
    assert p3c.window("JPM", "2023-Q2", "event", "W0") == ["2023-Q2"]
    assert "2024-Q2" in p3c.window("UBS", "2024-Q1", "earnings", "W2")
    assert all("annual" not in x for x in p3c.window("JPM", "2024-Q4", "earnings", "W2"))
