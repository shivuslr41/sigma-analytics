package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"os"

	SmartApi "github.com/angelbroking-github/smartapigo"
	"github.com/angelbroking-github/smartapigo/websocket"
	"github.com/xuri/excelize/v2"
)

// map columns of excel
type mapColumns int8
const (
	symbol mapColumns = iota
	boPrice
	bdPrice
	quantity
)

type angelToken struct {
	Token  string `json:"token"`
	Symbol string `json:"symbol"`
}

type tradeData struct {
	token                 string
	symbol                string
	orderType             string
	price                 float64
	breakOutTriggerPrice  float64
	breakDownTriggerPrice float64
	breakOutPrice         float64
	breakDownPrice        float64
	takeProfit            float64
	stopLoss              float64
	quantity              int64
	canPlaceOrder         bool
	placingOrder          bool
	executed              chan bool
	angelTradingClient    *SmartApi.Client
	angelMarketFeedClient *SmartApi.Client
	orderId               string
	socketClient          *websocket.SocketClient
	counter               float64
	tradeError            chan bool
}

func (t *tradeData) getSymbol() string {
	return fmt.Sprint(t.symbol, "-EQ")
}

var symbolMap = make(map[string]string)

func getTradeData() []*tradeData {
	resp, err := http.Get("https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json")
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}

	var tokens []angelToken
	err = json.Unmarshal(body, &tokens)
	if err != nil {
		fmt.Println("token fetch failed", err)
		os.Exit(1)
	}

	for _, token := range tokens {
		symbolMap[token.Symbol] = token.Token
	}

	return readAndPrepareData(getLatestFileLink()) //"https://api.telegram.org/file/bot1871366666:AAGpNZy9Kcyt_haOhslLH1t7RHqRgUqtn10/documents/file_1.xlsx"
}

func readAndPrepareData(link string) []*tradeData {
	resp, err := http.Get(link)
	if err != nil {
		fmt.Println("download file error", err)
		os.Exit(1)
	}
	f, err := excelize.OpenReader(resp.Body)
	if err != nil {
		fmt.Println("reading excel error", err)
		os.Exit(1)
	}
	defer func() {
		if err := f.Close(); err != nil {
			fmt.Println(err)
			os.Exit(1)
		}
	}()

	// Get all the rows in the Sheet1.
	rows, err := f.GetRows("Sheet1")
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}

	data := make([]*tradeData, len(rows)-1)
	for i, row := range rows {
		// ignore first row, usually headings
		if i == 0 {
			continue
		}
		tData := &tradeData{
			symbol:         row[symbol],
			breakOutPrice:  convertStrToFloat(row[boPrice]),
			breakDownPrice: convertStrToFloat(row[bdPrice]),
			quantity:       convertStrToInt(row[quantity]),
			executed:       make(chan bool),
			tradeError:     make(chan bool),
		}
		// map angel broking token to symbol
		tData.token = symbolMap[tData.getSymbol()]

		// set breakout and breakdown trigger price
		tData.breakOutTriggerPrice = tData.breakOutPrice * 0.999   // 0.1% down to actual buy price
		tData.breakDownTriggerPrice = tData.breakDownPrice * 1.001 // 0.1% up to actual sell price
		data[i-1] = tData
	}

	for i := range data {
		sendMessage(data[i].symbol + " - today's trade")
	}
	return data
}
