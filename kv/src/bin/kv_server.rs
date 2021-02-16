use kv;
use actix_web::{HttpServer, App, web};

fn main() {
    println!("KVFinder webserver started");

    // job timeout 30 minutes, expires after 1 day
    kv::webserver::create_ocypod_queue("kvfinder", "30m", "1d", 0);

    HttpServer::new(|| {
        App::new()
            .data(web::JsonConfig::default().limit(1_000_000))
            .route("/", web::get().to(kv::webserver::hello))
            .route("/{id}", web::get().to(kv::webserver::ask))
            .route("/create", web::post().to(kv::webserver::create)) 
    })
    .bind("0.0.0.0:8081")
    .expect("Cannot bind to port 8081")
    .run()
    .unwrap();
}
