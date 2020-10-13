import os, sys, toml, json, zlib, time
import requests
import dateutil.parser
from typing import Optional, Any, Dict


class Job(object):
    """ Create KVFinder-web job """

    def __init__(self, pdb: str, ligand_pdb: Optional[str]=None, probe_out: float=4.0, removal_distance: float=2.4):
        # Job Information (local)
        self.status: Optional[str] = None
        self.pdb: Optional[str] = pdb
        self.ligand: Optional[str] = ligand_pdb if ligand_pdb != None else None
        self.output_directory: Optional[str] = None
        self.base_name: Optional[str] = None
        self.id_added_manually: Optional[bool] = False
        
        # Request information (server)
        self.id: Optional[str] = None
        self.input: Optional[Dict[str, Any]] = {} 
        self.output: Optional[Dict[str, Any]] = None
        
        # Fill parameters and inputs
        self._default_settings(probe_out, removal_distance)
        self._add_pdb(pdb)
        if ligand_pdb != None:
            self._add_pdb(ligand_pdb, is_ligand=True)


    @property
    def cavity(self) -> Optional[Dict[str, Any]]:
        if self.output == None:
            return None
        else:
            return self.output["output"]["pdb_kv"]


    @property
    def report(self) -> Optional[Dict[str, Any]]:
        if self.output == None: 
            return None
        else:
            return self.output["output"]["report"]


    @property
    def log(self) -> Optional[Dict[str, Any]]:
        if self.output == None:
            return None
        else:
            return self.output["output"]["log"]


    def _add_pdb(self, pdb_fn: str, is_ligand: bool=False) -> None:
        with open(pdb_fn) as f:
            pdb = f.readlines()
        if is_ligand:
            self.input["pdb_ligand"] = pdb
        else:
            self.input["pdb"] = pdb


    def save(self, id: int) -> None:
        """ Save Job to job.toml """
        # Create job directory in ~/.KVFinder-web/
        job_dn = os.path.join(os.getcwd(), '.KVFinder-web', str(id))
        try:
            os.mkdir(job_dn)
        except FileExistsError:
            pass

        # Create job file inside ~/.KVFinder-web/id
        job_fn = os.path.join(job_dn, 'job.toml')
        with open(job_fn, 'w') as f:
            f.write("# TOML configuration file for KVFinder-web job\n\n")
            f.write("title = \"KVFinder-web job file\"\n\n")
            f.write(f"status = \"{self.status}\"\n\n")
            if self.id_added_manually:
                f.write(f"id_added_manually = true\n\n")
            f.write(f"[files]\n")
            if self.pdb is not None: 
                f.write(f"pdb = \"{self.pdb}\"\n")
            if self.ligand is not None:
                f.write(f"ligand = \"{self.ligand}\"\n")
            f.write(f"output = \"{self.output_directory}\"\n")
            f.write(f"base_name = \"{self.base_name}\"\n")
            f.write('\n')
            toml.dump(o=self.input['settings'], f=f)
            f.write('\n')


    @classmethod
    def load(cls, fn: Optional[str]):
        """ Load Job from job.toml """
        # Read job file
        with open(fn, 'r') as f:
            job = toml.load(f=f)

        pdb = job['files']['pdb']
        ligand_pdb = job['files']['ligand'] if 'ligand' in job['files'].keys() else None
        removal_distance = job['cutoffs']['removal_distance']
        probe_out = job['probes']['probe_out']

        return cls(pdb, ligand_pdb, probe_out, removal_distance)

    
    def export(self) -> None:
        # Prepare base file
        base_dir = os.path.join(self.output_directory, self.id)

        try:
            os.mkdir(base_dir)
        except FileExistsError:
            pass

        # Export cavity
        cavity_fn = os.path.join(base_dir, f'{self.base_name}.KVFinder.output.pdb')
        with open(cavity_fn, 'w') as f:
            f.write(self.cavity)

        # Export report
        report_fn = os.path.join(base_dir, f'{self.base_name}.KVFinder.results.toml')
        report = toml.loads(self.report)
        report['FILES_PATH']['INPUT'] = self.pdb
        report['FILES_PATH']['LIGAND'] = self.ligand
        report['FILES_PATH']['OUTPUT'] = cavity_fn
        with open(report_fn, 'w') as f:
            f.write('# TOML results file for parKVFinder software\n\n')
            toml.dump(o=report, f=f)
   
        # Export log
        log_fn = os.path.join(base_dir, 'KVFinder.log')
        with open(log_fn, 'w') as f:
            for line in self.log.split('\n'):
                if 'Running parKVFinder for: ' in line:
                    line = f'Running parKVFinder for job ID: {self.id}'
                    f.write(f'{line}\n')
                elif 'Dictionary: ' in line:
                    pass
                else:
                    f.write(f'{line}\n')

        # Export parameters
        if not self.id_added_manually:
            parameter_fn = os.path.join(self.output_directory, self.id, f'{self.base_name}_parameters.toml')
            with open(parameter_fn, 'w') as f:
                f.write("# TOML configuration file for KVFinder-web job.\n\n")
                f.write("title = \"KVFinder-web parameters file\"\n\n")
                f.write(f"[files]\n")
                f.write("# The path of the input PDB file.\n")
                f.write(f"pdb = \"{self.pdb}\"\n")
                f.write("# The path for the ligand's PDB file.\n")
                if self.ligand is not None:
                    f.write(f"ligand = \"{self.ligand}\"\n")
                else:
                    f.write(f"ligand = \"-\"\n")
                f.write('\n')
                f.write(f"[settings]\n")
                f.write(f"# Settings for cavity detection.\n\n")
                settings = {'settings': self.input['settings']}
                toml.dump(o=settings, f=f)
                f.write('\n')


    def _default_settings(self, probe_out: float, removal_distance: float):
        self.input["settings"] = {}
        self.input["settings"]["modes"] = {
            "whole_protein_mode" : True,
            "box_mode" : False,
            "resolution_mode" : "Low",
            "surface_mode" : True,
            "kvp_mode" : False,
            "ligand_mode" : False,
        }
        self.input["settings"]["step_size"] = {"step_size": 0.0}
        self.input["settings"]["probes"] = {
            "probe_in" : 1.4,
            "probe_out" : probe_out,
        }
        self.input["settings"]["cutoffs"] = {
            "volume_cutoff" : 5.0,
            "ligand_cutoff" : 5.0,
            "removal_distance" : removal_distance,
        }
        self.input["settings"]["visiblebox"] = {
            "p1" : {"x" : 0.00, "y" : 0.00, "z" : 0.00},
            "p2" : {"x" : 0.00, "y" : 0.00, "z" : 0.00},
            "p3" : {"x" : 0.00, "y" : 0.00, "z" : 0.00},
            "p4" : {"x" : 0.00, "y" : 0.00, "z" : 0.00},
        }
        self.input["settings"]["internalbox"] = {
            "p1" : {"x" : -4.00, "y" : -4.00, "z" : -4.00},
            "p2" : {"x" : 4.00, "y" : -4.00, "z" : -4.00},
            "p3" : {"x" : -4.00, "y" : 4.00, "z" : -4.00},
            "p4" : {"x" : -4.00, "y" : -4.00, "z" : 4.00},
        }


class Dataset(object):

    def __init__(self, filename: str="kv1000.zip", dirname: str="", is_zip=True):
        # Prepare dirname
        dirname = dirname + filename.replace('.zip', '')
        # Unzip files
        if is_zip:
            self.unzip(filename, dirname)
        # Get pdb list
        self.pdb_list = self.get_pdb_list(dirname)
        # Get statistics
        self.stats = self.get_statistics(dirname)

    @staticmethod
    def unzip(filename, dirname):
        from zipfile import ZipFile

        if not os.path.isdir(dirname):
            with ZipFile(filename, 'r') as f:
                f.extractall()

    @staticmethod
    def get_pdb_list(dirname):       
        return sorted([os.path.join(dirname, pdb) for pdb in os.listdir(dirname) if pdb.endswith('.pdb')])

    @staticmethod
    def get_statistics(dirname):
        from pandas import read_csv
        return read_csv(os.path.join(dirname, 'statistics.txt'), sep='\t')


class Sender(object):

    def __init__(self, server: str="http://localhost:8081"):
        # Define server
        self.server = f"{server}"

        # Create ./KVFinder-web directory for jobs
        try: 
            os.mkdir('.KVFinder-web')
        except FileExistsError:
            pass

        # Create time statistics file
        if not os.path.exists('results/time-statistics.txt'):
            with open('results/time-statistics.txt', 'w') as f:
                f.write('pdb\tid\tn_atoms\ttotal_time\telapsed_time\tworker_time\tn_workers\tjson_size\tprobe_out\tremoval_distance\n')

    def run(self, job: Job):
        if self._submit(job):
            # Save job
            job.status = 'queued'
            job.save(job.id)
        return

    def _submit(self, job) -> bool:
        r = requests.post(self.server + '/create', json=job.input)
        if r.ok:
            job.id = r.json()['id']
            job.output_directory = 'results'
            job.base_name = job.id
            return True
        else:
            # Write in erros.log
            with open('results/erros.log', 'a+') as log:
                log.write(f"\n>{pdb}\n")
                log.write(f"Probe Out: {job.input['settings']['probes']['probe_out']}\n")
                log.write(f"Removal Distance: {job.input['settings']['cutoffs']['removal_distance']}\n")
                log.write(r)     
            print("Debug:", r)
            return False


class Retriever(object):

    def __init__(self, server: str="http://localhost:8081", workers:int=1):
        # Define server
        self.server = f"{server}"
        
        # Register number of workers in KVFinder-web server
        self.workers = workers
    
    def start(self):

        # Get job IDs
        jobs = self._get_jobs()        
        
        while len(jobs) > 0:
            
            msg = f'> Checking {len(jobs)} jobs!'
            print(msg, end='', flush=True)
            
            for job_id in jobs:
                
                # Get job information
                job_fn = os.path.join('.KVFinder-web', job_id, 'job.toml')

                # Prepare job
                job = Job.load(fn=job_fn)
                job.id = job_id
                job.output_directory = 'results'
                job.base_name = job.id

                # Get results
                if self._get_results(job):
                    # total_time
                    total_time = dateutil.parser.parse(job.output['ended_at']) - dateutil.parser.parse(job.output['created_at'])
                    total_time = f'{total_time.total_seconds():4f}'
                    # elapsed_time
                    elapsed_time = dateutil.parser.parse(job.output['ended_at']) - dateutil.parser.parse(job.output['started_at'])
                    elapsed_time = f"{elapsed_time.total_seconds():4f}"
                    # worker_time
                    worker_time = dateutil.parser.parse(job.output['started_at']) - dateutil.parser.parse(job.output['created_at'])
                    worker_time = f"{worker_time.total_seconds():4f}"
                    # json_size
                    json_size = sys.getsizeof(json.dumps(job.output))
                    # n_atoms
                    n_atoms = get_number_of_atoms(job.pdb)
                    # po
                    po = job.input['settings']['probes']['probe_out']
                    # rd 
                    rd = job.input['settings']['cutoffs']['removal_distance']
                    
                    # Save statistics
                    with open('results/time-statistics.txt', 'a+') as out:
                        out.write(f'{job.pdb}\t{job.id}\t{n_atoms}\t{total_time}\t{elapsed_time}\t{worker_time}\t{json_size}\t{po}\t{rd}\t{self.workers}\n')

                    # Remove job from jobs list
                    jobs.remove(job_id)

                time.sleep(1)

            print(len(msg) * '\b', end='', flush=True)


    def _get_results(self, job) -> Optional[Dict[str, Any]]:
        
        r = requests.get(self.server + '/' + job.id)
                
        if r.ok:
            reply = r.json()
            if reply['status'] == 'completed' or reply['status'] == 'timed_out':
                # Pass output to job class
                job.output = reply
                job.status = reply['status']

                # Export results
                job.export()
                
                # Remove job directory
                job_dn = os.path.join('.KVFinder-web', job.id)
                self.erase_job_dir(job_dn)

                return True
        else:
            with open('results/thread.log', 'a+') as f:
                f.write(f">{job.id}\n")
                f.write(str(r) + '\n')
            return False

    @staticmethod
    def erase_job_dir(d) -> None:
        for f in os.listdir(d):
            f = os.path.join(d, f)
            if os.path.isdir(f):
                self.erase_job_dir(f)
            else:
                os.remove(f)
        os.rmdir(d)

    def _get_jobs(self) -> list:       
        return os.listdir('.KVFinder-web')

def get_number_of_atoms(pdb):
    from Bio.PDB import PDBParser
    # Read pdb
    parser = PDBParser(PERMISSIVE=1, QUIET=True)
    structure = parser.get_structure(f"{pdb.replace('kv1000/', '').replace('.pdb', '')}", pdb)
    # Count number of atoms
    n_atoms = 0
    for model in structure:
        for chain in model:
            for residue in chain:
                for atom in residue:
                    n_atoms += 1
    return n_atoms


if __name__ == "__main__":
    # Load Dataset Information
    dataset = Dataset()

    # Create results directory
    try: 
        os.mkdir('results')
    except FileExistsError:
        pass

    for workers in [1, 2, 3, 4]:

        print(f"[==> KV Server working with {workers} worker{'s' if workers > 1 else ''}")

        # Docker up
        os.system(f'docker-compose up -d --scale kv-worker={workers}')

        # Create and Configure Sender
        sender = Sender(server="http://localhost:8081")

        print("> Sending jobs to KV Server")

        # Send jobs to KV server
        for pdb in dataset.pdb_list:
            print(f'> {pdb}', end='', flush=True)       
            for po in [4.0, 6.0, 8.0]:
                job = Job(pdb=pdb, probe_out=po)
                sender.run(job)
            for rd in [0.0, 0.6, 1.2, 2.4]:
                job = Job(pdb=pdb, removal_distance=rd)
                sender.run(job)
            print('\b' * 19, end='', flush=True)
        
        time.sleep(60)

        print("> Retrieving jobs from KV Server")

        # Create and Configure Retriever
        retriever = Retriever(server="http://localhost:8081")
        # Start retriever
        retriever.start()

        # Erase .KVFinder-web
        os.system('rm -r .KVFinder-web')
