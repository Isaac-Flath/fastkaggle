# AUTOGENERATED! DO NOT EDIT! File to edit: ../00_core.ipynb.

# %% auto 0
__all__ = ['iskaggle', 'import_kaggle', 'setup_comp', 'nb_meta', 'push_notebook', 'check_ds_exists', 'mk_dataset', 'get_dataset',
           'get_pip_library', 'get_pip_libraries', 'push_dataset', 'get_local_ds_ver', 'create_libs_datasets',
           'create_requirements_dataset']

# %% ../00_core.ipynb 3
import os,json,subprocess, shutil
import re
from fastcore.utils import *
# from fastcore.all import *

# %% ../00_core.ipynb 4
iskaggle = os.environ.get('KAGGLE_KERNEL_RUN_TYPE', '')

# %% ../00_core.ipynb 5
def import_kaggle():
    "Import kaggle API, using Kaggle secrets `kaggle_username` and `kaggle_key` if needed"
    if iskaggle:
        from kaggle_secrets import UserSecretsClient
        sec = UserSecretsClient()
        os.environ['KAGGLE_USERNAME'] = sec.get_secret("kaggle_username")
        if not os.environ['KAGGLE_USERNAME']: raise Exception("Please insert your Kaggle username and key into Kaggle secrets")
        os.environ['KAGGLE_KEY'] = sec.get_secret("kaggle_key")
    from kaggle import api
    return api

# %% ../00_core.ipynb 7
def setup_comp(competition, install=''):
    "Get a path to data for `competition`, downloading it if needed"
    if iskaggle:
        if install:
            os.system(f'pip install -Uqq {install}')
        return Path('../input')/competition
    else:
        path = Path(competition)
        api = import_kaggle()
        if not path.exists():
            import zipfile
            api.competition_download_cli(str(competition))
            zipfile.ZipFile(f'{competition}.zip').extractall(str(competition))
        return path

# %% ../00_core.ipynb 10
def nb_meta(user, id, title, file, competition=None, private=True, gpu=False, internet=True, linked_datasets=[]):
    "Get the `dict` required for a kernel-metadata.json file"
    d = {
      "id": f"{user}/{id}",
      "title": title,
      "code_file": file,
      "language": "python",
      "kernel_type": "notebook",
      "is_private": private,
      "enable_gpu": gpu,
      "enable_internet": internet,
      "keywords": [],
      "dataset_sources": linked_datasets,
      "kernel_sources": []
    }
    if competition: d["competition_sources"] = [f"competitions/{competition}"]
    return d

# %% ../00_core.ipynb 12
def push_notebook(user, id, title, file, path='.', competition=None, private=True, gpu=False, internet=True, linked_datasets=[]):
    "Push notebook `file` to Kaggle Notebooks"
    meta = nb_meta(user, id, title, file=file, competition=competition, private=private, gpu=gpu, internet=internet, linked_datasets=[])
    path = Path(path)
    nm = 'kernel-metadata.json'
    path.mkdir(exist_ok=True, parents=True)
    with open(path/nm, 'w') as f: json.dump(meta, f, indent=2)
    api = import_kaggle()
    api.kernels_push_cli(str(path))

# %% ../00_core.ipynb 16
def check_ds_exists(dataset_slug # Dataset slug (ie "zillow/zecon")
                   ):
    '''Checks if a dataset exists in kaggle and returns boolean'''
    api = import_kaggle()
    ds_search = L(api.dataset_list(mine=True)).filter(lambda x: str(x)==dataset_slug)
    if len(ds_search)==1: return True
    elif len(ds_search)==0: return False
    else: raise exception("Multiple datasets found - Check Manually")

# %% ../00_core.ipynb 17
def mk_dataset(dataset_path, # Local path to create dataset in
               title, # Name of the dataset
               force=False, # Should it overwrite or error if exists?
               upload=True # Should it upload and create on kaggle
              ):
    '''Creates minimal dataset metadata needed to push new dataset to kaggle'''
    dataset_path = Path(dataset_path)
    dataset_path.mkdir(exist_ok=force,parents=True)
    api = import_kaggle()
    api.dataset_initialize(dataset_path)
    md = json.load(open(dataset_path/'dataset-metadata.json'))
    md['title'] = title
    md['id'] = md['id'].replace('INSERT_SLUG_HERE',title)
    json.dump(md,open(dataset_path/'dataset-metadata.json','w'))
    if upload: (dataset_path/'empty.txt').touch()
    api.dataset_create_new(str(dataset_path),public=True,dir_mode='zip',quiet=True)

# %% ../00_core.ipynb 19
def get_dataset(dataset_path, # Local path to download dataset to
                dataset_slug, # Dataset slug (ie "zillow/zecon")
                unzip=True, # Should it unzip after downloading?
                force=False # Should it overwrite or error if dataset_path exists?
               ):
    '''Downloads an existing dataset and metadata from kaggle'''
    if not force: assert not Path(dataset_path).exists()
    api = import_kaggle()
    api.dataset_metadata(dataset_slug,str(dataset_path))
    api.dataset_download_files(dataset_slug,str(dataset_path))
    if unzip:
        zipped_file = Path(dataset_path)/f"{dataset_slug.split('/')[-1]}.zip"
        import zipfile
        with zipfile.ZipFile(zipped_file, 'r') as zip_ref:
            zip_ref.extractall(Path(dataset_path))
        zipped_file.unlink()
    

# %% ../00_core.ipynb 20
def get_pip_library(dataset_path, # Local path to download pip library to
                    pip_library, # name of library for pip to install
                    pip_cmd="pip" # pip base to use (ie "pip3" or "pip")
                   ):    
    '''Download the whl files for pip_library and store in dataset_path'''
    bashCommand = f"{pip_cmd} download {pip_library} -d {dataset_path}"
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()

# %% ../00_core.ipynb 21
def get_pip_libraries(dataset_path, # Local path to download pip library to
                    requirements_path, # path to requirements file
                      pip_cmd="pip" # pip base to use (ie "pip3" or "pip")
                     ):
    '''Download whl files for a requirements.txt file and store in dataset_path'''
    bashCommand = f"{pip_cmd} download -r {requirements_path} -d {dataset_path}"
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()

# %% ../00_core.ipynb 23
def push_dataset(dataset_path, # Local path where dataset is stored 
                 version_comment # Comment associated with this dataset update
                ):
    '''Push dataset update to kaggle.  Dataset path must contain dataset metadata file'''
    api = import_kaggle()
    api.dataset_create_version(str(dataset_path),version_comment,dir_mode='zip',quiet=True)

# %% ../00_core.ipynb 24
def get_local_ds_ver(lib_path, # Local path dataset is stored in
                     lib # Name of library (ie "fastcore")
                    ):
    '''checks a local copy of kaggle dataset for library version number'''
    wheel_lib_name = lib.replace('-','_')
    local_path = (lib_path/f"library-{lib}")
    lib_whl = local_path.ls().filter(lambda x: wheel_lib_name in x.name.lower())
    if 1==len(lib_whl):
        return re.search(f"(?<={wheel_lib_name}-)[\d+.]+\d",lib_whl[0].name.lower())[0]
    elif 0<len(local_path.ls().filter(lambda x: 'dist' in x.name)):
        lib_whl = (local_path/'dist').ls().filter(lambda x: wheel_lib_name in x.name.lower())
        if 1==len(lib_whl):
            return re.search(f"(?<={wheel_lib_name}-)[\d+.]+\d",lib_whl[0].name.lower())[0]
    return None

# %% ../00_core.ipynb 26
def create_libs_datasets(libs, # library or list of libraries to create datasets for (ie 'fastcore or ['fastcore','fastkaggle']
                         lib_path, # Local path to dl/create dataset
                         username, # You username
                         clear_after=False # Delete local copies after sync with kaggle?
                        ):
    '''For each library, create or update a kaggle dataset with the latest version'''
    if type(libs)==str: libs = [libs] 
    
    retain = ["dataset-metadata.json"]
    for lib in libs:
        title = f"library-{lib}"
        local_path = lib_path/title
        print(f"{lib} | Processing as {title} at {local_path}")
        if Path(local_path).exists(): shutil.rmtree(local_path)

        print(f"{lib} | Downloading or Creating Dataset")
        try: get_dataset(local_path,f"{username}/{title}",force=True)
        except Exception as ex:
            if '404' in str(ex): mk_dataset(local_path,title,force=True)
            else: raise ex
            
        print(f"{lib} | Checking dataset version against pip")
        ver_local_orig = get_local_ds_ver(lib_path,lib)

        for item in local_path.ls():
            if item.name not in retain: 
                if item.is_dir(): shutil.rmtree(item)
                else: item.unlink()
        get_pip_library(local_path,lib)
        ver_local_new = get_local_ds_ver(lib_path,lib)
        if (ver_local_new != ver_local_orig) or (ver_local_new==None and ver_local_orig==None): 
            print(f"{lib} | Updating {lib} in Kaggle from {ver_local_orig} to {ver_local_new}")
            
            push_dataset(local_path,ifnone (ver_local_new, "Version Unknown"))
        else: print(f"{lib} | Kaggle dataset already up to date {ver_local_orig} to {ver_local_new}")
        if clear_after: shutil.rmtree(local_path)
        print(f"{lib} | Complete")

# %% ../00_core.ipynb 27
def create_requirements_dataset(req_fpath, # Path to requirements.txt file
                                lib_path,#Local path to dl/create dataset
                                title, # Title you want the kaggle dataset named
                                username, # you username
                                retain = ["dataset-metadata.json"], # Files that should not be removed
                                version_notes = "New Update"
                               ):
    '''Download everything needed in a `requirements.txt` file to a dataset and upload to kaggle'''
    local_path = lib_path/title
    print(f"Processing {title} at {local_path}")
    if Path(local_path).exists(): shutil.rmtree(local_path)

    print(f"-----Downloading or Creating Dataset")
    if check_ds_exists(f"{username}/{title}"): 
        get_dataset(local_path,f"{username}/{title}",force=True)
    else:                                       
        mk_dataset(local_path,title,force=True)

    print(f"-----Checking dataset version against pip")
    orig_ds = Path(local_path).ls().sorted()
    for item in local_path.ls():
        if item.name not in retain: 
            if item.is_dir(): shutil.rmtree(item)
            else: item.unlink()
    get_pip_libraries(local_path,req_fpath) 
    
    new_ds = Path(local_path).ls().sorted()
    
    if orig_ds != new_ds: 
        print(f"-----Updating {title} in Kaggle")
        push_dataset(local_path,version_notes)
    else: print(f"-----Kaggle dataset already up to date")
    print('Complete')
