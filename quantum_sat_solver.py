#import matplotlib.pyplot as plt
#%matplotlib inline
import numpy as np
import pylab
import sys
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister
from qiskit import execute, IBMQ
from qiskit.tools.monitor import job_monitor
from qiskit.tools.visualization import plot_histogram, circuit_drawer

# Set your API Token.
# You can get it from https://quantumexperience.ng.bluemix.net/qx/account,
# looking for "Personal Access Token" section.
QX_TOKEN = ""
#QX_URL = "https://quantumexperience.ng.bluemix.net/api"

# Authenticate with the IBM Q API in order to use online devices.
# You need the API Token and the QX URL.
IBMQ.enable_account(QX_TOKEN)

sat_formula = [[-1,-2,-3],[-1,2,3],[-1,2,-3]]
n_clauses = len(sat_formula)

n_literals = 3

q_input = QuantumRegister(n_literals)
q_auxiliar = QuantumRegister(n_clauses-2)
q_extra = QuantumRegister(n_clauses)
q_output = QuantumRegister(1)
ans = ClassicalRegister(n_literals)
qc = QuantumCircuit(q_input,q_output,q_auxiliar,q_extra,ans)

def initialization(q_circuit, q_in, extra, n_literals, n_clauses):
	for i in range(n_literals):
		q_circuit.h(q_in[i])
	for j in range(n_clauses):
		q_circuit.x(extra[j])

def circuit_constr(q_circuit,q_in,clausula):
	for literal in clausula:
		if(literal > 0):
			q_circuit.x(q_in[literal - 1])


def send_to_extra(q_circuit,q_in,q_auxiliar,q_extra,c):
	q_circuit.ccx(q_in[0],q_in[1],q_auxiliar[0])
	q_circuit.ccx(q_in[2],q_auxiliar[0],q_extra[c])
	q_circuit.ccx(q_in[0],q_in[1],q_auxiliar[0])

def junction(q_circuit,q_extra,q_auxiliar,q_output,n_clauses):
	if(n_clauses == 3):
		q_circuit.ccx(q_extra[0],q_extra[1],q_auxiliar[0])
		q_circuit.ccx(q_extra[2],q_auxiliar[0],q_output[0])

	elif(n_clauses == 4):
		q_circuit.ccx(q_extra[0],q_extra[1],q_auxiliar[0])
		q_circuit.ccx(q_extra[2],q_auxiliar[0],q_auxiliar[1])
		q_circuit.ccx(q_extra[3],q_auxiliar[1],q_output[0])

	elif(n_clauses > 4):
		q_circuit.ccx(q_extra[0],q_extra[1],q_auxiliar[0])
		k=1
		for i in range(2,n_clauses-1):
			q_circuit.ccx(q_extra[i],q_auxiliar[k-1],q_auxiliar[k])
			k=k+1
		q_circuit.ccx(q_extra[n_clauses-1],q_auxiliar[n_clauses-3],q_output[0])

def junction_inversion(q_circuit,q_extra,q_auxiliar,n_clauses):
	if(n_clauses == 3):
			q_circuit.ccx(q_extra[0],q_extra[1],q_auxiliar[0])

	elif(n_clauses == 4):
		q_circuit.ccx(q_extra[2],q_auxiliar[0],q_auxiliar[1])
		q_circuit.ccx(q_extra[0],q_extra[1],q_auxiliar[0])

	elif(n_clauses > 4):
		k = n_clauses - 3
		for i in reversed(range(2,n_clauses - 1)):
			q_circuit.ccx(q_extra[i],q_auxiliar[k-1],q_auxiliar[k])
			k = k - 1
		q_circuit.ccx(q_extra[0],q_extra[1],q_auxiliar[0])

def circuit_inversion(q_circuit,q_in,q_auxiliar,q_extra,sat_formula,n_literals):
	aux_counter = n_clauses-1
	for claus in reversed(sat_formula):
		circuit_constr(q_circuit,q_in,claus)
		send_to_extra(q_circuit,q_in,q_auxiliar,q_extra,aux_counter)
		aux_counter = aux_counter -1
		circuit_constr(q_circuit,q_in,claus)

def finalization(q_circuit,q_in,q_output,q_auxiliar,n_literals):
	for i in range(n_literals):
		q_circuit.h(q_in[i])
		q_circuit.x(q_in[i])
	q_circuit.x(q_output[0])
	q_circuit.h(q_output[0])
	q_circuit.ccx(q_in[0],q_in[1],q_auxiliar[0])
	q_circuit.ccx(q_in[2],q_auxiliar[0],q_output[0])
	q_circuit.ccx(q_in[0],q_in[1],q_auxiliar[0])
	for i in range(n_literals):
		q_circuit.x(q_in[i])
		q_circuit.h(q_in[i])
	q_circuit.h(q_output[0])
	q_circuit.x(q_output[0])
	q_circuit.h(q_output[0])

def measuring(q_circuit,q_in,ans):
	q_circuit.measure(q_in,ans)



def formula_rep(q_circuit,q_in,q_auxiliar,q_extra,sat_formula):
	for c,claus in enumerate(sat_formula):
		circuit_constr(q_circuit,q_in,claus)
		send_to_extra(q_circuit,q_in,q_auxiliar,q_extra,c)
		circuit_constr(q_circuit,q_in,claus)


initialization(qc,q_input,q_extra,n_literals,n_clauses)

formula_rep(qc,q_input,q_auxiliar,q_extra,sat_formula)

junction(qc,q_extra,q_auxiliar,q_output,n_clauses)

junction_inversion(qc,q_extra,q_auxiliar,n_clauses)

circuit_inversion(qc,q_input,q_auxiliar,q_extra,sat_formula,n_literals)

finalization(qc,q_input,q_output,q_auxiliar,n_literals)

measuring(qc,q_input,ans)


# See a list of available local simulators
print("IBMQ backends: ", IBMQ.backends())

backend_ibmq = IBMQ.get_backend('ibmq_qasm_simulator')
job_ibmq = execute(qc, backend_ibmq)
job_monitor(job_ibmq)

result_ibmq = job_ibmq.result()


circuit_drawer(qc).save("circuit.pdf", "PDF")
x = plot_histogram(result_ibmq.get_counts(qc))
x.savefig("out_quantum.png")

# Show the results
print(result_ibmq.get_counts(qc))