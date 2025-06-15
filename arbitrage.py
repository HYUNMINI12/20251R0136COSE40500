import ccxt
import time

# 거래소 객체 생성
binance = ccxt.binance()
kraken = ccxt.kraken()

# 가격 차이 임계값 (예: 0.5%)
SPREAD_THRESHOLD = 0.005


def get_price(exchange, symbol="BTC/USDT"):
    """ 특정 거래소에서 BTC/USDT 가격을 가져오는 함수 """
    try:
        ticker = exchange.fetch_ticker(symbol)
        return ticker['last']
    except Exception as e:
        print(f"{exchange.id}에서 가격을 가져오는 중 오류 발생: {e}")
        return None


def check_arbitrage():
    """ 두 거래소 간 가격 차이를 계산하고 아비트라지 기회를 찾는 함수 """
    price_binance = get_price(binance)
    price_kraken = get_price(kraken)

    if price_binance and price_kraken:
        spread = abs(price_binance - price_kraken) / min(price_binance, price_kraken)

        print(f"Binance 가격: {price_binance}, Kraken 가격: {price_kraken}, 스프레드: {spread:.4%}")

        if spread > SPREAD_THRESHOLD:
            if price_binance > price_kraken:
                print("Kraken에서 매수하고 Binance에서 매도!")
            else:
                print("Binance에서 매수하고 Kraken에서 매도!")
        else:
            print("아비트라지 기회 없음.")


# 주기적으로 실행
while True:
    check_arbitrage()
    time.sleep(5)  # 5초마다 체크
