// Local setup and one foreground crawl. No owner password or account is created.
package main

import (
	"flag"
	"fmt"
	"github.com/stjudewashere/seonaut/internal/models"
	"github.com/stjudewashere/seonaut/internal/repository"
	"github.com/stjudewashere/seonaut/internal/services"
	"log"
	"net"
	"time"
)

func main() {
	config := flag.String("c", "config", "Configuration file")
	crawl := flag.Bool("crawl", false, "Crawl Fraser Fix after creating the five projects")
	flag.Parse()
	if conn, err := net.DialTimeout("tcp", "127.0.0.1:9000", time.Second); err == nil {
		conn.Close()
		log.Fatal("Stop the SEOnaut app LaunchAgent before running setup, then restart it after the crawl completes.")
	}
	c := services.NewContainer(*config)
	db, err := repository.SqlConnect(c.Config.DB)
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()
	sites := []string{"https://www.fraserfixmechanical.com", "https://www.pick-card.com", "https://www.invitescafe.com", "https://www.enanto.com", "https://www.mobillify.com"}
	for _, site := range sites {
		var count int
		if err := db.QueryRow("SELECT COUNT(*) FROM projects WHERE url=?", site).Scan(&count); err != nil {
			log.Fatal(err)
		}
		if count == 0 {
			_, err = db.Exec("INSERT INTO projects (url,user_id,crawl_sitemap,user_agent) VALUES (?,NULL,1,?)", site, c.Config.Crawler.Agent)
			if err != nil {
				log.Fatal(err)
			}
		}
	}
	// Transfer these unowned projects when the owner creates their own account.
	var triggers int
	if err := db.QueryRow("SELECT COUNT(*) FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE() AND TRIGGER_NAME='claim_owner_projects'").Scan(&triggers); err != nil {
		log.Fatal(err)
	}
	if triggers == 0 {
		_, err = db.Exec("CREATE TRIGGER claim_owner_projects AFTER INSERT ON users FOR EACH ROW UPDATE projects SET user_id=NEW.id WHERE user_id IS NULL AND LOWER(NEW.email)='harchaind@gmail.com'")
		if err != nil {
			log.Fatal(err)
		}
	}
	fmt.Println("Five projects ready, waiting for owner registration")
	if !*crawl {
		return
	}
	var p models.Project
	if err = db.QueryRow("SELECT id,url FROM projects WHERE url=?", sites[0]).Scan(&p.Id, &p.URL); err != nil {
		log.Fatal(err)
	}
	p.CrawlSitemap = true
	p.UserAgent = c.Config.Crawler.Agent
	done := make(chan struct{}, 1)
	c.PubSubBroker.NewSubscriber(fmt.Sprintf("crawl-%d", p.Id), func(m *models.Message) error {
		if m.Name == "CrawlEnd" {
			done <- struct{}{}
		}
		return nil
	})
	if err = c.CrawlerService.StartCrawler(p, models.BasicAuth{}); err != nil {
		log.Fatal(err)
	}
	<-done
	fmt.Println("Fraser Fix crawl completed")
}
