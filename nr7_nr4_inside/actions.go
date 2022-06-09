package main

import (
	"fmt"
	"strings"
	"time"

	SmartApi "github.com/angelbroking-github/smartapigo"
)

// place order
func (t *tradeData) placeOrder() {
	// create session
	_ = createNewSession(t.angelTradingClient)

	t.placingOrder = true
	maxRetries := 10
	i := 0
	for i = 0; i < maxRetries; i++ {
		order, err := t.angelTradingClient.PlaceOrder(
			SmartApi.OrderParams{
				Variety:         "NORMAL",
				TradingSymbol:   t.getSymbol(),
				SymbolToken:     t.token,
				TransactionType: t.orderType,
				Exchange:        "NSE",
				OrderType:       "LIMIT",
				ProductType:     "INTRADAY",
				Duration:        "DAY",
				Price:           fmt.Sprintf("%.2f", t.price),
				SquareOff:       fmt.Sprintf("%.2f", t.takeProfit),
				StopLoss:        fmt.Sprintf("%.2f", t.stopLoss),
				Quantity:        fmt.Sprintf("%d", t.quantity),
			},
		)
		if err != nil {
			fmt.Println(t.symbol, "error placing order", err)
			time.Sleep(5 * time.Second)
			continue
		}
		t.orderId = order.OrderID
		break
	}
	if maxRetries == i {
		fmt.Println("max retries attemped..", t.symbol)
		close(t.tradeError)
		return
	}
	fmt.Println("order placed", t.symbol)
	sendMessage("order placed for: " + t.symbol)

	// check order status
	maxRetries = 10
	for i = 0; i < maxRetries; i++ {
		p, err := t.angelTradingClient.GetPositions()
		fmt.Println("GetPositions", p, err, t.symbol)
		tb, err := t.angelTradingClient.GetTradeBook()
		fmt.Println("GetTradeBook", tb, err, t.symbol)
		orders, err := t.angelTradingClient.GetOrderBook()
		fmt.Println("GetOrderBook", orders, err, t.symbol)
		if err != nil {
			fmt.Println("get order book error", err)
			time.Sleep(5 * time.Second)
			continue
		}
		for _, o := range orders {
			if t.orderId == o.OrderID {
				if strings.Contains(strings.ToLower(o.OrderStatus), "completed") ||
					strings.Contains(strings.ToLower(o.OrderStatus), "executed") {
					fmt.Println("order executed", t.symbol)
					close(t.executed)
					return
				}
			}
		}
		break
	}
	if maxRetries == i {
		fmt.Println("max retries attemped..", t.symbol)
		close(t.tradeError)
		return
	}
}
