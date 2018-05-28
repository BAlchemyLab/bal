# Block[Chain] Alchemy Laboratory Framework

The source code of originally based on post on [Building a Blockchain](https://medium.com/p/117428612f46) of Daniel van Flymen. 

## Installation

1. Make sure [Python](https://www.python.org/downloads/) 2 or 3 is installed. 


2. Install requirements (preferably inside a [virtual environment](https://docs.python.org/3/tutorial/venv.html)).  

```
$ pip install -r requirements.txt
``` 

5. Run the server:
    * `$ python2 blockchain.py -p 5001 -d pow.db -v pow:2`
    * `$ python3 blockchain.py --port 5002 --db quant.db --variant quant`
    
## Parameters

    '-p', '--port', default=5000, type=int, help='port to listen on'
    '-d', '--db', default='', help='db file, if not passed, then no persistance'
    '-v', '--variant', default='pow', help='variant of blockchain "pow[:difficulty]" or "quant", where:
          * pow[:difficulty] -- POWBlockChain with possibility of "difficulty" setting (4 by default)
          * quant -- QuantumBlockChain

For QuantumBlockChain, the [keyworker](https://github.com/BAlchemyLab/qnet/tree/master/keyworker) service must be started.

## Testing
Internal test:
```
python -m unittest tests.test_BaseBlockChain
```

Test REST API POW:
1. Run blockchain.py servers on ports 5000 and 5001 with POW variant.
2. Run test script:
```
./tests/test.sh
```

Test REST API QUANTUM:
1. Run blockchain.py servers on ports 5000 and 5001 with quantum variants.
2. Run [keyworker](https://github.com/BAlchemyLab/qnet/tree/master/keyworker) on port 55554
2. Run test script:
```
./tests/testquantum.sh
```

## Blockchain Mininet network
Mininet's custom setup for BAL classes balmn.py add several types of hosts:
* btc -- bcnode.BtcNode
* eth -- bcnode.EthNode
* pow -- bcnode.POWNode
* qkd -- bcnode.QNode

For example:
```
mn --custom=balmn.py --host=btc
```

Testing:
```
./bcmn_test.py [host_type]
```


**Test with quantum links:**
```bash
mn --custom=bal/QKCustom.py --link=qk --topo=tree,depth=2,fanout=3
```

**Test with ryu:**

```bash
sudo mn --custom bal/topo_2sw-2host.py --topo mytopo --mac --controller remote --switch ovs
```

Go to 'bal' directory and start ryu-manager:

```bash
cd bal
sudo ryu-manager rest_forward.py
```

You can switch channels with RestAPI:
For raw channel:
```bash
curl -X GET http://localhost:8080/channel/1/1
```
For quantum channel:
```bash
curl -X GET http://localhost:8080/channel/1/2
```

## More information
you may find in the project's [Wiki](https://github.com/BAlchemyLab/bal/wiki).
