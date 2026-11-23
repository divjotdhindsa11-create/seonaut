package routes

import (
	"encoding/json"
	"html/template"
	"net/http"
	"os"
	"strings"
)

func (h *projectHandler) overviewHandler(w http.ResponseWriter, r *http.Request) {
	user, ok := h.CookieSession.GetUser(r.Context())
	if !ok {
		http.Error(w, "Sign in required", 401)
		return
	}
	if !strings.EqualFold(user.Email, os.Getenv("SEONAUT_OWNER_EMAIL")) {
		http.Error(w, "Owner access required", 403)
		return
	}
	raw, err := os.ReadFile(os.Getenv("SEONAUT_OVERVIEW_FILE"))
	if err != nil {
		http.Error(w, "Data refresh pending", 503)
		return
	}
	var snapshot interface{}
	if json.Unmarshal(raw, &snapshot) != nil {
		http.Error(w, "Invalid snapshot", 503)
		return
	}
	t, err := template.ParseFiles("web/templates/overview.html")
	if err != nil {
		http.Error(w, "Dashboard unavailable", 500)
		return
	}
	w.Header().Set("Cache-Control", "no-store")
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	_ = t.Execute(w, struct {
		Snapshot interface{}
		Projects interface{}
	}{snapshot, h.ProjectViewService.GetProjectViews(user.Id)})
}
