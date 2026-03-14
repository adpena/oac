package main

import (
    "encoding/json"
    "os"
)

type payload struct {
    Event  string `json:"event"`
    Tool   string `json:"tool"`
    Status string `json:"status"`
    Note   string `json:"note"`
}

func main() {
    out := payload{
        Event:  "post-hydrate",
        Tool:   "oac",
        Status: "ok",
        Note:   "go starter hook placeholder",
    }
    _ = json.NewEncoder(os.Stdout).Encode(out)
}
