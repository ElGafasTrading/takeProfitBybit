import config
import time
from pybit.unified_trading import HTTP
from decimal import Decimal, ROUND_DOWN, ROUND_FLOOR

symbol = ''  # Puedes ajustar el símbolo según tus necesidades
take_profit = 0  # Valor porcentaje
estado = False
precio_position = 0
order_id = ''

session = HTTP(
    testnet=False,
    api_key=config.api_key,
    api_secret=config.api_secret,
)


def qty_step(symbol, price):
    step = session.get_instruments_info(category="linear", symbol=symbol)
    ticksize = float(step['result']['list'][0]['priceFilter']['tickSize'])
    scala_precio = int(step['result']['list'][0]['priceScale'])
    precision = Decimal(f"{10**scala_precio}")
    tickdec = Decimal(f"{ticksize}")
    precio_final = (Decimal(f"{price}")*precision)/precision
    precide = precio_final.quantize(Decimal(f"{1/precision}"),rounding=ROUND_FLOOR)
    operaciondec = (precide / tickdec).quantize(Decimal('1'), rounding=ROUND_FLOOR) * tickdec
    result = float(operaciondec)

    return result

def cancelar_take_profit(symbol, orderid):
    print('CANCELANDO TAKE PROFIT')
    order = session.cancel_order(
        category="linear",
        symbol=symbol,
        orderId=orderid,
    )

    return order

def establecer_take_profit(symbol, price, side, qty):
    price = qty_step(symbol, price)
    print(price)

    if side == 'Buy':
        side = 'Sell'
    else:
        side = 'Buy'

    # PONER ORDEN TAKE PROFIT
    order = session.place_order(
        category="linear",
        symbol=symbol,
        side=side,
        orderType="Limit",
        reduceOnly=True,
        qty=qty,
        price=price,
    )

    order_id = order['result']['orderId']
    print(order_id)

    return order_id


while True:
    try:
        if estado:
            # Posiciones Abiertas
            posiciones = session.get_positions(category="linear", symbol=symbol)
            if float(posiciones['result']['list'][0]['avgPrice']) != 0:
                precio_de_entrada = float(posiciones['result']['list'][0]['avgPrice'])
                precio_take = 0
                if posiciones['result']['list'][0]['side'] == 'Buy':
                    precio_take = ((precio_de_entrada * take_profit)/100)+precio_de_entrada
                else:
                    precio_take = precio_de_entrada-((precio_de_entrada * take_profit)/100)
                if precio_take < 0:
                    print('TU STOP LOSS NO ES POSIBLE, SE ENCUENTRA POR DEBAJO DE CERO')
                else:
                    # poner take profit
                    if precio_position != precio_de_entrada:
                        print(isinstance(order_id, str))
                        print(order_id)
                        if order_id != '':
                            cancelar_take_profit(symbol, order_id)

                        print('MODIFICANDO TAKE PROFIT')
                        side = posiciones['result']['list'][0]['side']
                        qty = float(posiciones['result']['list'][0]['size'])
                        order_id = establecer_take_profit(symbol, precio_take, side, qty)
                        precio_position = precio_de_entrada
            else:
                session.cancel_all_orders(category="linear", symbol=symbol)
                estado = False
                precio_position = 0
                order_id = ''

        else:
            tick = input('INGRESE EL TICK QUE DESEA OPERAR: ').upper()
            if tick != '':
                tick = tick + 'USDT'
                symbol = tick
                take_profit = float(input('INGRESE EL PORCENTAJE QUE DESEA TOMAR LAS GANANCIAS: '))
                if take_profit != '':
                    # Posiciones Abiertas
                    posiciones = session.get_positions(category="linear", symbol=symbol)
                    if float(posiciones['result']['list'][0]['avgPrice']) != 0:
                        print('POSICION ABIERTA EN ' + symbol)
                        estado = True

                    else:
                        print('NO HAY NINGUNA POSICION ABIERTA EN ' + symbol)
                else:
                    print('EL DATO INGRESADO NO ES VALIDO')
            else:
                print('EL DATO INGRESADO NO ES VALIDO')

    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)
    time.sleep(1)
