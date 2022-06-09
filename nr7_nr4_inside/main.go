package main

import (
	"fmt"
	"os"
	"sync"
	"time"

	SmartApi "github.com/angelbroking-github/smartapigo"
)

func main() {
	username := ""
	password := ""
	tradingAPIKey := ""
	marketFeedAPIKey := ""

	// Create New Angel Broking Client
	angelTradingClient := SmartApi.New(username, password, tradingAPIKey)
	angelMarketFeedClient := SmartApi.New(username, password, marketFeedAPIKey)

	// logout
	defer logout(angelTradingClient, angelMarketFeedClient)

	// terminate process after 3:15 PM, assuming cronjob is set to run every day 9:15 AM
	go func() {
		expired := time.After(6 * time.Hour)
		<-expired
		fmt.Println("Done for the day, time expired", time.Now())
		logout(angelTradingClient, angelMarketFeedClient)
		os.Exit(0)
	}()

	wg := sync.WaitGroup{}
	for _, td := range getTradeData() {
		wg.Add(1)
		td.angelTradingClient = angelTradingClient
		td.angelMarketFeedClient = angelMarketFeedClient

		// stream market data and trade
		go trade(td, &wg)
	}
	wg.Wait()
	fmt.Println("done for the day, all trades are placed", time.Now())
	sendMessage("done for the day, all trades are placed")
}

func logout(clients ...*SmartApi.Client) {
	for i := range clients {
		clients[i].Logout()
	}
}