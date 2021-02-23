mod kv {
    use serde::{Deserialize, Serialize};

    #[derive(Serialize, Deserialize, Debug)]
    struct KVParameters {
        title: String,
        files_path: KVFilesPath,
        settings: KVSettings,
    }

    #[derive(Serialize, Deserialize, Debug)]
    struct KVFilesPath {
        dictionary: String,
        pdb: String,
        output: String,
        base_name: String,
        ligand: String,
    }

    #[derive(Serialize, Deserialize, Debug, Clone)]
    struct KVSettings {
        modes: KVSModes,
        step_size: KVSStepSize,
        probes: KVSProbes,
        cutoffs: KVSCutoffs,
        visiblebox: KVSVisiblebox,
        internalbox: KVSInternalbox,
    }

    #[derive(Serialize, Deserialize, Debug, Clone)]
    struct KVSModes {
        whole_protein_mode: bool,
        box_mode: bool,
        resolution_mode: KVSResolution, 
        surface_mode: bool,
        kvp_mode: bool,
        ligand_mode: bool,
    }

    #[derive(Serialize, Deserialize, Debug, Clone)]
    enum KVSResolution {
        Low,
        Medium,
        High,
    }

    #[derive(Serialize, Deserialize, Debug, Clone)]
    struct KVSStepSize {
        step_size: f64,
    }

    #[derive(Serialize, Deserialize, Debug, Clone)]
    struct KVSProbes {
        probe_in: f64,
        probe_out: f64,
    }

    #[derive(Serialize, Deserialize, Debug, Clone)]
    struct KVSCutoffs {
        volume_cutoff: f64,
        ligand_cutoff: f64,
        removal_distance: f64,
    }

    #[derive(Serialize, Deserialize, Debug, Clone)]
    struct KVSVisiblebox {
        p1: KVSBoxPoint,
        p2: KVSBoxPoint,
        p3: KVSBoxPoint,
        p4: KVSBoxPoint,
    }

    #[derive(Serialize, Deserialize, Debug, Clone)]
    struct KVSInternalbox {
        p1: KVSBoxPoint,
        p2: KVSBoxPoint,
        p3: KVSBoxPoint,
        p4: KVSBoxPoint,

    }

    #[derive(Serialize, Deserialize, Debug, Clone)]
    struct KVSBoxPoint {
        x: f64, 
        y: f64,
        z: f64,
    }

    struct PdbBoundaries {
        x_min: f64,
        x_max: f64,
        y_min: f64,
        y_max: f64,
        z_min: f64,
        z_max: f64,
    }

    #[derive(Serialize, Deserialize, Debug)]
    pub struct Input {
        settings: KVSettings,
        pdb: Vec<String>,
        pdb_ligand: Option<Vec<String>>,
    }

    impl Input {
        fn get_pdb_boundaries(&self) -> PdbBoundaries {
            //TODO
            PdbBoundaries {
                x_min : 0.0,
                x_max : 0.0,
                y_min : 0.0,
                y_max : 0.0,
                z_min : 0.0,
                z_max : 0.0,
            }
        }
    }

    #[derive(Serialize, Deserialize, Debug, Clone)]
    pub struct Output {
        pdb_kv: String,
        report: String,
        log: String,
        msg: String,
    }

    #[derive(Serialize, Deserialize)]
    struct Data {
        tags: [String;1],
        input: Input,
        msg: String,
    }

    pub mod worker {
        use std::io;
        use std::io::Write;
        use reqwest;
        use std::process::Command;
        use std::fs;
        use toml;
        use serde::{Deserialize, Serialize};
        use std::path::Path;
        use std::fs::{File,create_dir};
        use super::{Input, Output};

        #[derive(Serialize, Deserialize, Debug)]
        pub struct JobInput {
            pub id: u32,
            input: Input,
        }

        #[derive(Serialize, Deserialize, Debug, Clone)]
        struct JobOutput {
            status: String,
            output: Output,
        }

        pub struct Config {
            pub kv_path: String,
            pub job_path: String,
        }

        impl JobInput {
            fn save(&self, config: &Config) -> Result<(), io::Error> {
                self.input.save(self.id, &config)?;
                Ok(())
            }
    
            fn run(&self, config: &Config) -> Result<Output, io::Error> {
                let kvfinder = Command::new(format!("{}/parKVFinder", config.kv_path))
                                    .current_dir(format!("{}/{}", config.job_path, self.id))
                                    .arg("-p")
                                    .arg("params.toml")
                                    .status()
                                    .expect("failed to execute KVFinder process");
                println!("process exited with: {}", kvfinder);
                if kvfinder.success() {
                    let output = Output { 
                        pdb_kv:  fs::read_to_string(format!("{}/{}/KV_Files/KVFinderWeb/KVFinderWeb.KVFinder.output.pdb", config.job_path, self.id))?,
                        report:  fs::read_to_string(format!("{}/{}/KV_Files/KVFinderWeb/KVFinderWeb.KVFinder.results.toml", config.job_path, self.id))?, 
                        log: fs::read_to_string(format!("{}/{}/KV_Files/KVFinder.log", config.job_path, self.id))?, 
                        msg: String::new(),
                    };
                    println!("KVFinder OK");
                    return Ok(output);
                } else {
                    return Err(io::Error::new(io::ErrorKind::Other, "oh no! check if variable KVFinder_PATH was set"));
                }
            }
        }
   
        impl Input {
            fn save(&self, id: u32, config: &Config) -> Result<(), io::Error> {
                let dir = format!("{}/{}", config.job_path, id);
                match create_dir(&dir) {
                    Err(err) => Err(err),
                    Ok(_) => {
                        self.save_parameters(&dir, &config)?;
                        self.save_pdb(&dir)?;
                        if let Some(_) = self.pdb_ligand {
                            self.save_pdb_ligand(&dir)?;
                        }
                        Ok(())
                    },
                }
            }
    
            fn save_parameters(&self, dir: &str, config: &Config) -> Result<(), io::Error> {
                let params = super::KVParameters{
                    title: String::from("KVFinder-worker parameters"),
                    files_path: super::KVFilesPath{
                        dictionary: String::from(format!("{}/dictionary", config.kv_path)),
                        pdb: String::from("./protein.pdb"),
                        ligand: String::from("./ligand.pdb"),
                        output: String::from("./"),
                        base_name: String::from("KVFinderWeb"),
                    },
                    settings: self.settings.clone(),
                };
                let toml_parameters = toml::to_string(&params);
                let filename = format!("{}/params.toml", dir);
                let path = Path::new(&filename);
                let mut file = File::create(path)?;
                if let Ok(p) = toml_parameters {
                    writeln!(file, "{}", p)?;
                }
                Ok(())
            }
    
            fn save_pdb(&self, dir: &str) -> Result<(), io::Error> {
                let filename = format!("{}/protein.pdb", dir);
                let path = Path::new(&filename);
                let mut file = File::create(path)?;
                writeln!(file, "{}", self.pdb.join(""))?;
                Ok(())
            }
    
            fn save_pdb_ligand(&self, dir: &str) -> Result<(), io::Error> {
                let filename = format!("{}/ligand.pdb", dir);
                let path = Path::new(&filename); 
                let mut file = File::create(&path)?;
                if let Some(pdb_ligand) = &self.pdb_ligand {
                    writeln!(file, "{}", pdb_ligand.join(""))?;
                }
                Ok(())
            }
        }

        pub fn get_job() -> Result<JobInput, reqwest::Error> {
            // let j: JobInput = reqwest::get("http://0.0.0.0:8023/queue/kvfinder/job")?.json()?;
            let j: JobInput = reqwest::get("http://ocypod:8023/queue/kvfinder/job")?.json()?;
            Ok(j)
        }

        pub fn process(job: JobInput, config: &Config) -> Result<Output, io::Error> {
            job.save(&config)?;
            let output = job.run(&config); 
            output
        }

        pub fn submit_result(id: u32, output: Output) -> Result<u32, reqwest::Error> {
            let client = reqwest::Client::new();
            // let url = format!("http://0.0.0.0:8023/job/{}", id);
            let url = format!("http://ocypod:8023/job/{}", id);
            let data = JobOutput {
                status: String::from("completed"),
                output,
            };
            let _result = client.patch(url.as_str())
                .json(&data)
                .send()?;
            Ok(id)
        }
    }

    pub mod webserver {
        use actix_web::{web, Responder, HttpResponse};
        use reqwest;
        use serde_json;
        use serde_json::json;
        use fasthash::city;
        use serde::{Deserialize, Serialize};
        use super::{Input, Output, Data};

        #[derive(Serialize, Deserialize)]
        struct Job {
            #[serde(default)]
            id: String,     // this id is the same as tag_id (NOT queue_id)
            status: String,
            output: Option<Output>,
            created_at: String,
            started_at: Option<String>,
            ended_at: Option<String>, 
            expires_after: String,
        }


        #[derive(Serialize, Deserialize)]
        struct QueueConfig<'a> {
            timeout: &'a str,
            expires_after: &'a str,
            retries: i32,
        }
        

        pub fn hello() -> impl Responder {
            "KVFinder Web"
        }


        pub fn create_ocypod_queue(queue_name: &str, timeout: &str, expires_after: &str, retries: i32) {
            let client = reqwest::Client::new();
            let queue_url = format!("http://ocypod:8023/queue/{}", queue_name);
            let queue_config = QueueConfig { timeout, expires_after, retries };
            let _response = client.put(&queue_url)
                .json(&queue_config)
                .send();
            // match _response {
            //     Ok(_) => HttpResponse::Ok().json(json!({"id":data.tags[0]})),
            //     Err(e) => HttpResponse::InternalServerError().body(format!("{:?}", e)),
            // }
        }
        
        fn get_queue_id(tag_id: &String) -> Result<Option<u32>, reqwest::Error> {
            // let url = format!("http://0.0.0.0:8023/tag/{}", tag_id);
            let url = format!("http://ocypod:8023/tag/{}", tag_id);

            // ids because in theory could be more than one with the same tag, BUT if this happen there is an error 
            // if tag_id (hash64) not found in queue Ok(None)
            // if request fail return Err (possible problem in queue server)
            let mut ids: Vec<u32> = reqwest::get(url.as_str())?.json()?; 
            // pop returns last id (should have only one or zero) or None
            Ok(ids.pop())
        }
        
        fn get_job(tag_id: String) -> Result<Option<Job>, reqwest::Error> {
            let queue_id = get_queue_id(&tag_id);
            let job = |queue_id| {
                // let url = format!("http://0.0.0.0:8023/job/{}?fields=status,output,created_at,started_at,ended_at,expires_after", queue_id);
                let url = format!("http://ocypod:8023/job/{}?fields=status,output,created_at,started_at,ended_at,expires_after", queue_id);
                let mut j: Job = reqwest::get(url.as_str())?.json()?;
                j.id = tag_id;
                Ok(Some(j))
            };
         
            match queue_id {
                    Err(e) => Err(e),
                    // if queue_id is None (tag_id not found) 
                    Ok(None) => return Ok(None),
                    // return job data in json
                    Ok(Some(queue_id)) => return job(queue_id), 
            }
        }
        
        fn check(input: &Input) -> Result<(), String> {
            Ok(())
        }

        pub fn ask(id: web::Path<String>) -> impl Responder {
            let tag_id = id.into_inner();
            let job = get_job(tag_id);
            match job {
                Err(e) => HttpResponse::InternalServerError().body(format!("{:?}", e)),
                Ok(None) => HttpResponse::NotFound().finish(),
                Ok(Some(j)) => HttpResponse::Ok().json(j),
            }
        }

        pub fn create(job_input: web::Json<Input>) -> impl Responder {
            // json input values to inp
            let input = job_input.into_inner();
            if let Err(e) = check(&input) {
                return HttpResponse::BadRequest().body(format!("{:?}", e));
            }
            let data = Data {
                // create a tag using function hash64 applied to input (unique value per input)
                tags: [city::hash64(serde_json::to_string(&input).unwrap()).to_string()],
                input,
                msg: String::from("Testing notification\nThere are a new plugin version available, please download it from our github to use new features!"),
            };
            let create_job = || {
                let client = reqwest::Client::new();
                // let res = client.post("http://0.0.0.0:8023/queue/kvfinder/job")
                let response = client.post("http://ocypod:8023/queue/kvfinder/job")
                    .json(&data)
                    .send();
                match response {
                    Ok(_) => HttpResponse::Ok().json(json!({"id":data.tags[0], "msg": data.msg})),
                    Err(e) => HttpResponse::InternalServerError().body(format!("{:?}", e)),
                }
            };
            let job = get_job(data.tags[0].clone());
            match job {
                // if err, problem in queue server
                Err(e) => HttpResponse::InternalServerError().body(format!("{:?}", e)),
                // if job with this tag is in queue, return job 
                Ok(Some(j)) => HttpResponse::Ok().json(j),
                // if job with this tag is not found on queue, create job
                Ok(None) => create_job(), //format!("{} created", tag_id),
            }
        }

    }
}

pub use crate::kv::worker;
pub use crate::kv::webserver;    
