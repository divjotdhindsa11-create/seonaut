package routes

import (
	"bytes"
	"html/template"
	"strings"
	"testing"
)

func TestOverviewTemplateProtectsEmbeddedData(t *testing.T) {
	tmpl, err := template.ParseFiles("../../web/templates/overview.html")
	if err != nil {
		t.Fatal(err)
	}
	var buf bytes.Buffer
	err = tmpl.Execute(&buf, struct {
		Snapshot interface{}
		Projects interface{}
	}{map[string]interface{}{"sites": []string{"</script><script>alert(1)</script>"}}, nil})
	if err != nil {
		t.Fatal(err)
	}
	if strings.Contains(buf.String(), "</script><script>alert(1)</script>") || strings.Contains(buf.String(), "ZgotmplZ") {
		t.Fatal("Unsafe or rejected JavaScript template data")
	}
}
