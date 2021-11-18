# IIS project - Public transport system

## Project setup
### Download
1. `git clone git@github.com:petak5/IIS.git`
2. `cd IIS/`

### Install dependencies
1. `cd src/`
2. `pipenv install` (run on first run or after Pipfile was changed)

### Configure
1. `cp .env_example .env`
2. Modify configuration in `.env` using text editor of your choice

### Create tables
1. `pipenv shell`
2. `flask db init`
3. `flask db migrate`
4. `flask db upgrade`
5. `exit`

**Note:** Steps 3 and 4 have to be re-ran after any changes to db model

### Run
1. `pipenv run python run.py`
