package main

import (
	"fmt"
	"os"
	"time"

	SmartApi "github.com/angelbroking-github/smartapigo"
)

var wait = make(chan bool, 1)

func createNewSession(angelClient *SmartApi.Client) SmartApi.UserSession {
	wait <- true
	// User Login and Generate User Session
	session, err := angelClient.GenerateSession()
	if err != nil {
		fmt.Println("gen sess error", err)
		os.Exit(1)
	}

	//Renew User Tokens using refresh token
	session.UserSessionTokens, err = angelClient.RenewAccessToken(session.RefreshToken)
	if err != nil {
		fmt.Println("renew user token error", err)
		os.Exit(1)
	}

	//Get User Profile
	session.UserProfile, err = angelClient.GetUserProfile()
	if err != nil {
		fmt.Println("get profile error", err)
		os.Exit(1)
	}
	// fmt.Println("User Profile :- ", session.UserProfile)
	// fmt.Println("User Session Object :- ", session)
	time.Sleep(1 * time.Second)
	<-wait
	return session
}
