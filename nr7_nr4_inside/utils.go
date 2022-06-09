package main

import (
	"fmt"
	"os"
	"strconv"
	"time"
)

// convert str to float
func convertStrToFloat(s string) float64 {
	if f, err := strconv.ParseFloat(s, 64); err == nil {
		return f
	} else {
		fmt.Println(err)
		os.Exit(1)
	}
	return 0
}

// convert str to int
func convertStrToInt(s string) int64 {
	if f, err := strconv.ParseInt(s, 0, 64); err == nil {
		return f
	} else {
		fmt.Println(err)
		os.Exit(1)
	}
	return 0
}

// today's date timestamp
func todaysDate() int64 {
	return time.Date(time.Now().Year(), time.Now().Month(), time.Now().Day(), 0, 0, 0, 0, time.UTC).Unix()
}
