import ccxt
import time

# 가격 차이 임계값 (예: 0.5%)
SPREAD_THRESHOLD = 0.005

# 한국의 주요 암호화폐 거래소 목록
KOREAN_EXCHANGES = ["upbit", "bithumb", "coinone", "korbit", "gopax"]


def get_korean_exchange_prices(symbol="BTC/USDT"):
    """ 한국 주요 거래소의 BTC/USDT 가격을 가져옴 """
    prices = {}

    for exchange_id in KOREAN_EXCHANGES:
        try:
            exchange = getattr(ccxt, exchange_id)()
            if "fetch_ticker" in dir(exchange):  # 가격 조회 기능 확인
                ticker = exchange.fetch_ticker(symbol)
                prices[exchange_id] = ticker['last']
        except Exception as e:
            print(f"⚠ {exchange_id}에서 가격을 가져오는 중 오류 발생: {e}")
            continue

    return prices


def find_arbitrage_opportunity(prices):
    """ 가격이 가장 낮은 거래소와 높은 거래소를 찾아 아비트라지 기회를 확인 """
    if not prices:
        print("가격 데이터를 가져올 수 없습니다.")
        return

    min_exchange = min(prices, key=prices.get)  # 최저 가격 거래소
    max_exchange = max(prices, key=prices.get)  # 최고 가격 거래소
    min_price = prices[min_exchange]
    max_price = prices[max_exchange]

    spread = (max_price - min_price) / min_price

    print(f"\n📊 최저가: {min_exchange} ({min_price:.2f} USDT), 최고가: {max_exchange} ({max_price:.2f} USDT)")
    print(f"🔍 가격 차이 (스프레드): {spread:.4%}")

    if spread > SPREAD_THRESHOLD:
        print(f"🚀 아비트라지 기회 발견! [{min_exchange}]에서 매수하고 [{max_exchange}]에서 매도하세요!")
    else:
        print("⚠ 아비트라지 기회가 없습니다.")


# 주기적으로 실행
while True:
    print("\n🔄 거래소 가격 업데이트 중...")
    prices = get_korean_exchange_prices()
    find_arbitrage_opportunity(prices)
    time.sleep(10)  # 10초마다 업데이트