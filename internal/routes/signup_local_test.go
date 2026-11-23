package routes

import (
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"
)

func TestLocalSignupClosed(t *testing.T) {
	t.Setenv("SEONAUT_SIGNUP_OPEN", "false")
	h := &userHandler{}
	for _, method := range []string{"GET", "POST"} {
		w := httptest.NewRecorder()
		r := httptest.NewRequest(method, "/signup", nil)
		if method == "GET" {
			h.signupGetHandler(w, r)
		} else {
			h.signupPostHandler(w, r)
		}
		if w.Code != 403 {
			t.Fatalf("%s status=%d", method, w.Code)
		}
	}
}
func TestLocalSignupClosedMarker(t *testing.T) {
	t.Setenv("SEONAUT_SIGNUP_OPEN", "true")
	marker := filepath.Join(t.TempDir(), "closed")
	t.Setenv("SEONAUT_SIGNUP_CLOSED_FILE", marker)
	if err := os.WriteFile(marker, []byte("closed"), 0600); err != nil {
		t.Fatal(err)
	}
	h := &userHandler{}
	for _, method := range []string{"GET", "POST"} {
		w := httptest.NewRecorder()
		r := httptest.NewRequest(method, "/signup", nil)
		if method == "GET" {
			h.signupGetHandler(w, r)
		} else {
			h.signupPostHandler(w, r)
		}
		if w.Code != 403 {
			t.Fatalf("%s status=%d", method, w.Code)
		}
	}
}
