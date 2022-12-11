package main

import (
	"C"
	"log" 
	//"encoding/json"
	"net/http"
	"github.com/gorilla/mux"
	"time"
)

// #cgo pkg-config: python-2.7
// #include <Python.h>

type App struct { 
    Router *mux.Router
}

func handleGetRequestsHome(w http.ResponseWriter, r *http.Request) { 
    log.Println(r)
} 


func handleGetRequestPage(w http.ResponseWriter, r *http.Request) { 
	params := mux.Vars(r)
	pageId := params["pageId"]
	log.Println(pageId)
} 

func (a *App) Run(addr string) {
    log.Println("Starting server at", addr);
    
    a.Router = mux.NewRouter()
    a.Router.HandleFunc("/", handleGetRequestsHome)
    a.Router.HandleFunc("/{pageId}", handleGetRequestPage)
    srv := &http.Server{
	Handler: a.Router, 
	Addr: addr,
	WriteTimeout: 15 * time.Second,
	ReadTimeout: 15 * time.Second,
    }

    log.Fatal(srv.ListenAndServe())
}

//export startPyFronServer 
func startPyFronServer(pythonHandler *C) { 
    a := App{}
    a.Run(":8000")
}

func main() { 
}
