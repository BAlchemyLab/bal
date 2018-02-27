#!/bin/sh

BC=blockchain.py
NODE0="http://localhost:5000"
NODE1="http://localhost:5001"
KEYWORKER="http://localhost:55554"

# Adding keyworkers
echo curl -s -X POST -H "Content-Type: application/json" -d '{ "keyworkers": [{"address":"'$KEYWORKER'","id":0}] }' $NODE0/keyworker/register
curl -s -X POST -H "Content-Type: application/json" -d '{ "keyworkers": [{"address":"'$KEYWORKER'","id":0}] }' $NODE0/keyworker/register
echo curl -s -X POST -H "Content-Type: application/json" -d '{ "keyworkers": [{"address":"'$KEYWORKER'","id":0}] }' $NODE1/keyworker/register
curl -s -X POST -H "Content-Type: application/json" -d '{ "keyworkers": [{"address":"'$KEYWORKER'","id":0}] }' $NODE1/keyworker/register


# Adding and removing nodes
echo curl $NODE0/nodes
curl $NODE0/nodes
echo curl -s -X POST -H "Content-Type: application/json" -d '{ "nodes": [{"address":"'$NODE1'","keyworker_id":0}] }' $NODE0/nodes/register
curl -s -X POST -H "Content-Type: application/json" -d '{ "nodes": [{"address":"'$NODE1'","keyworker_id":0}] }' $NODE0/nodes/register
echo curl $NODE0/nodes
curl $NODE0/nodes
echo curl -s -X DELETE -H "Content-Type: application/json" http://localhost:5000/nodes
curl -s -X DELETE -H "Content-Type: application/json" http://localhost:5000/nodes
echo curl $NODE0/nodes
curl $NODE0/nodes
echo curl -s -X POST -H "Content-Type: application/json" -d '{ "nodes": [{"address":"'$NODE1'","keyworker_id":0}] }' $NODE0/nodes/register
curl -s -X POST -H "Content-Type: application/json" -d '{ "nodes": [{"address":"'$NODE1'","keyworker_id":0}] }' $NODE0/nodes/register
echo curl $NODE0/nodes
curl $NODE0/nodes

ADDR0=`curl -s -X GET -H "Content-Type: application/json" $NODE0/mine | grep recipient | sed 's/^.*: "\([a-f0-9]*\)",.*$/\1/'`
echo ADDR0=$ADDR0
ADDR1=`curl -s -X GET -H "Content-Type: application/json" $NODE1/mine | grep recipient | sed 's/^.*: "\([a-f0-9]*\)",.*$/\1/'`
echo ADDR1=$ADDR1
echo
echo Sending 5 from ADDR0 to ADDR1:
echo
echo curl -s -X POST -H "Content-Type: application/json" -d '{ "sender": "'$ADDR0'", "recipient": "'$ADDR1'", "amount": 5 }' $NODE1/transactions/new
curl -s -X POST -H "Content-Type: application/json" -d '{ "sender": "'$ADDR0'", "recipient": "'$ADDR1'", "amount": 5 }' $NODE1/transactions/new
echo
echo curl -s -X GET -H "Content-Type: application/json" $NODE0/mine
curl -s -X GET -H "Content-Type: application/json" $NODE0/mine
echo
echo curl -s -X GET -H "Content-Type: application/json" $NODE0/chain
curl -s -X GET -H "Content-Type: application/json" $NODE0/chain 2>&1 | tee /tmp/n1.log
echo
echo Sending 10 from ADDR1 to ADDR0:
echo
echo curl -s -X POST -H "Content-Type: application/json" -d '{ "sender": "'$ADDR1'", "recipient": "'$ADDR0'", "amount": 10 }' $NODE1/transactions/new
curl -s -X POST -H "Content-Type: application/json" -d '{ "sender": "'$ADDR1'", "recipient": "'$ADDR0'", "amount": 10 }' $NODE1/transactions/new
echo
echo curl -s -X GET -H "Content-Type: application/json" $NODE1/mine
curl -s -X GET -H "Content-Type: application/json" $NODE1/mine
echo
echo curl -s -X GET -H "Content-Type: application/json" $NODE1/mine
curl -s -X GET -H "Content-Type: application/json" $NODE1/mine
echo
echo curl -s -X GET -H "Content-Type: application/json" $NODE1/mine
curl -s -X GET -H "Content-Type: application/json" $NODE1/mine
echo
echo curl -s -X GET -H "Content-Type: application/json" $NODE0/nodes/resolve
curl -s -X GET -H "Content-Type: application/json" $NODE0/nodes/resolve
echo
echo curl -s -X GET -H "Content-Type: application/json" $NODE0/chain
curl -s -X GET -H "Content-Type: application/json" $NODE0/chain 2>&1 | tee /tmp/n2.log
echo
if cmp -s /tmp/n1.log /tmp/n2.log
then
 echo Test is not passed -- the chain was not changed.
else
 echo Test passed -- the chain was changed.
fi
