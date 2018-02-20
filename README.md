# Block[Chain] Alchemy Laboratory Framework

The source code of originally based on post on [Building a Blockchain](https://medium.com/p/117428612f46) of Daniel van Flymen. 

## Installation

1. Make sure [Python 3.6+](https://www.python.org/downloads/) is installed. 
2. Install [pipenv](https://github.com/kennethreitz/pipenv). 

```
$ pip3.6 install pipenv 
```

3. Create a _virtual environment_ and specify the Python version to use. 

```
$ pipenv --python=python3.6
```

4. Install requirements.  

```
$ pipenv install 
``` 

5. Run the server:
    * `$ pipenv run python blockchain.py` 
    * `$ pipenv run python blockchain.py -p 5001`
    * `$ pipenv run python blockchain.py --port 5002`
    
## Parameters

    '-p', '--port', default=5000, type=int, help='port to listen on'
    '-k', '--kwport', default=55554, type=int, help='port keyworker to listen on'
    '-i', '--ip', default='127.0.0.1', help='ip keyworker to listen on'
    '-d', '--db', default='', help='db file, if not passed, then no persistance'
    '-v', '--variant', default='pow', help='variant of blockchain "pow[:difficulty]" or "quant", where:
          * pow[:difficulty] -- POWBlockChain with possibility of "difficulty" setting (4 by default)
          * quant -- QuantumBlockChain

For QuantumBlockChain, the [keyworker](https://github.com/BAlchemyLab/qnet/tree/master/keyworker) service must be started.

## Testing
```
pipenv run python -m unittest tests.test_BaseBlockChain
```
```
./tests/test.sh
```
