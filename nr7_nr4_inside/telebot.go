package main

import (
	"fmt"
	"os"
	"strings"
	"time"

	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

const chatId = 0000 // channel id

func botToken() string {
	return "valid-bot-token"
}

// creates bot session
func newBot() *tgbotapi.BotAPI {
	bot, err := tgbotapi.NewBotAPI(botToken())
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
	bot.Debug = true
	return bot
}

// gets latest uploaded file of the present day
func getLatestFileLink() string {
	bot := newBot()
	u := tgbotapi.NewUpdate(0)
	updateList, err := bot.GetUpdates(u)
	if err != nil {
		fmt.Println("getUpdates error", err)
		os.Exit(1)
	}

	// store recent uploaded file id
	lastFileId := ""
	for _, update := range updateList {
		if update.ChannelPost != nil {
			// collect fileId based on date and file type(spreadsheet)
			if update.ChannelPost.Document == nil ||
				int64(update.ChannelPost.Date) < todaysDate() ||
				!strings.Contains(update.ChannelPost.Document.MimeType, "spreadsheetml") {
				continue
			}
			lastFileId = update.ChannelPost.Document.FileID
		}
	}
	if lastFileId != "" {
		f, err := bot.GetFile(tgbotapi.FileConfig{
			FileID: lastFileId,
		})
		if err != nil {
			fmt.Println("getFile error", err)
			os.Exit(1)
		}
		return f.Link(botToken())
	}
	fmt.Println("Looks like file is not uploaded today, Exit 0", time.Now())
	sendMessage("Looks like no trade day")
	os.Exit(0)

	// code never reach here
	return ""
}

// buffered channel to limit sending 1 message/second
var sendLimit = make(chan bool, 1)

// send trade updates to channel
func sendMessage(msg string) {
	go func() {
		sendLimit <- true
		bot := newBot()
		message := tgbotapi.NewMessage(chatId, msg)
		_, err := bot.Send(message)
		if err != nil {
			fmt.Println("sendMsg error", err)
			return
		}
		time.Sleep(1*time.Second)
		<-sendLimit
	}()
}
