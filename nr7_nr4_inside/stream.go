package main

import (
	"fmt"
	"math"
	"sync"
	"time"

	"github.com/angelbroking-github/smartapigo/websocket"
)

// Triggered when any error is raised
func (t *tradeData) onError(err error) {
	fmt.Println("socket error: ", err, t.symbol)
}

// Triggered when websocket connection is closed
func (t *tradeData) onClose(code int, reason string) {
	fmt.Println("socket close: ", code, reason)
}

// Triggered when connection is established and ready to send and accept data
func (t *tradeData) onConnect() {
	err := t.socketClient.Subscribe()
	if err != nil {
		fmt.Println("socket subscribe error", err, t.symbol)
	}
	fmt.Println("subscribe success", t.symbol, time.Now())
}

// Triggered when a message is received
func (t *tradeData) onMessage(message []map[string]interface{}) {
	t.counter++
	if math.Mod(t.counter, 100) == 0 {
		fmt.Println("message from: ", t.symbol)
		fmt.Printf("message Received :- %v\n", message)
	}
	for _, m := range message {
		if t.placingOrder {
			continue
		}
		sltp, ok := m["ltp"].(string)
		if !ok {
			continue
		}
		ltp := convertStrToFloat(sltp)
		if ltp == 0 {
			continue
		}
		// ltp shd be between triggerprice and 0.5% down/up to triggerprice
		if ltp <= t.breakOutTriggerPrice && ltp >= t.breakOutTriggerPrice*0.995 && !t.canPlaceOrder {
			t.canPlaceOrder = true
			fmt.Println("triggered buy order: ", t.symbol, t.breakOutTriggerPrice, ltp)
			sendMessage("triggered buy order: " + t.symbol + " at " + sltp)
		} else if ltp >= t.breakDownTriggerPrice && ltp <= t.breakDownTriggerPrice*1.005 && !t.canPlaceOrder {
			t.canPlaceOrder = true
			fmt.Println("triggered sell order: ", t.symbol, t.breakDownTriggerPrice, ltp)
			sendMessage("triggered sell order: " + t.symbol + " at " + sltp)
		}
		if !t.canPlaceOrder {
			continue
		}
		// ltp can be slight above buy price , not too above and vice versa for sell side
		if ltp >= t.breakOutPrice && ltp <= t.breakOutPrice*1.005 {
			// t.canPlaceOrder = false
			t.orderType = "BUY"
			t.price = t.breakOutPrice
			// set target and stoploss
			t.takeProfit = t.breakOutPrice * 1.01 // 1% target
			t.stopLoss = t.breakOutPrice * 0.99   // 1% stoploss
			fmt.Println("placing buy order: ", t.symbol, t.breakOutPrice, ltp)
			sendMessage("placing buy order: " + t.symbol + " at " + sltp)
			// blocking call
			t.placeOrder()
		} else if ltp <= t.breakDownPrice && ltp >= t.breakDownPrice*0.995 {
			// t.canPlaceOrder = false
			t.orderType = "SELL"
			t.price = t.breakDownPrice
			// set target and stoploss
			t.takeProfit = t.breakDownPrice * 0.99 // 1% target
			t.stopLoss = t.breakDownPrice * 1.01   // 1% stoploss
			fmt.Println("placing sell order: ", t.symbol, t.breakDownPrice, ltp)
			sendMessage("placing sell order: " + t.symbol + " at " + sltp)
			// blocking call
			t.placeOrder()
		}
	}
}

// Triggered when reconnection is attempted which is enabled by default
func (t *tradeData) onReconnect(attempt int, delay time.Duration) {
	fmt.Printf("reconnect attempt %d in %fs\n", attempt, delay.Seconds())
}

// Triggered when maximum number of reconnect attempt is made and the program is terminated
func (t *tradeData) onNoReconnect(attempt int) {
	fmt.Printf("maximum no of reconnect attempt reached: %d\n", attempt)
}

func trade(t *tradeData, wg *sync.WaitGroup) {
	defer wg.Done()
	for {
		func() {
			closer := make(chan bool)
			defer func() {
				if r := recover(); r != nil {
					fmt.Println("panic occured in outer func: ", r, t.symbol, time.Now())
					close(closer)
				}
			}()

			session := createNewSession(t.angelMarketFeedClient)
			// New Websocket Client
			socketClient := websocket.New(session.ClientCode, session.FeedToken, "nse_cm|"+t.token)
			// Assign callbacks
			socketClient.OnError(t.onError)
			socketClient.OnClose(t.onClose)
			socketClient.OnMessage(t.onMessage)
			socketClient.OnConnect(t.onConnect)
			socketClient.OnReconnect(t.onReconnect)
			socketClient.OnNoReconnect(t.onNoReconnect)
			socketClient.SetReconnectMaxRetries(math.MaxInt)
			socketClient.SetReconnectMaxDelay(10 * time.Second)
			socketClient.SetAutoReconnect(true)
			t.socketClient = socketClient

			go func() {
				defer func() {
					if r := recover(); r != nil {
						fmt.Println("panic occured in serve func: ", r, t.symbol, time.Now())
						close(closer)
					}
				}()
				t.socketClient.Serve()
			}()

			select {
			case <-t.executed:
				fmt.Println("successfully executed: ", t.symbol)
				sendMessage("successfully executed: " + t.symbol)
			case <-t.tradeError:
				fmt.Println("trade error for", t.symbol)
				sendMessage("trade error for: " + t.symbol)
			case <-closer:
				fmt.Println("closer called", t.symbol)
			}
			socketClient.Close()
		}()
		if t.placingOrder {
			break
		}
	}
	fmt.Println("completed: ", t.symbol, time.Now())
}
