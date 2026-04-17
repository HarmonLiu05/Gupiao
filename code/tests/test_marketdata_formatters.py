from polybot.clients.yahoo_market_data import StockQuote
from polybot.marketdata.formatters import format_records


def test_format_records_as_json():
    rows = [StockQuote(symbol="AAPL", last_price="212.34", currency="USD")]

    output = format_records(rows, output="json")

    assert '"symbol": "AAPL"' in output
    assert '"last_price": "212.34"' in output


def test_format_records_as_csv():
    rows = [StockQuote(symbol="AAPL", last_price="212.34", currency="USD")]

    output = format_records(rows, output="csv")

    assert "symbol,last_price,currency" in output
    assert "AAPL,212.34,USD" in output


def test_format_records_as_table():
    rows = [StockQuote(symbol="AAPL", last_price="212.34", currency="USD")]

    output = format_records(rows, output="table")

    assert "symbol\tlast_price\tcurrency" in output
    assert "AAPL\t212.34\tUSD" in output
