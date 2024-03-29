import logging
    # app.logger.warning('testing warning log')
    # app.logger.error('testing error log')
    # app.logger.info('testing info log')
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests
import json
import os
from dotenv import load_dotenv

# Carica le variabili di ambiente dal file .env
dotenv_path = os.path.join(os.path.dirname(__file__), '../.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

app = Flask(__name__)
CORS(app)

# Leggi l'endpoint dall'ambiente
endpoint = os.getenv('ENDPOINT') 

@app.route('/')
def index():
    return render_template('index.html')

import logging
from flask import jsonify

@app.route('/drugs', methods=['GET'])
def drugsNames():
    try:
        query = """
            PREFIX schema: <https://schema.org/>
            PREFIX mesh: <https://www.ncbi.nlm.nih.gov/mesh/?term=>
            PREFIX drug: <https://drugcentral.org/drugcard/>
            PREFIX file: <https://clinicaltrials.gov/ct2/show/>

            SELECT DISTINCT ?drugName
            WHERE {
            ?drug a schema:Drug ;
                    schema:name ?drugName .
            }
            """

        payload = {'query': query}

        # Set the headers
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        # Make the POST request
        response = requests.post(endpoint, data=payload, headers=headers)

        if response.status_code == 200:
            result = response.json()
            # Return JSON response
            return jsonify(result)
        else:
            return jsonify({'error': 'Failed to get a valid response'}), 500

    except Exception as e:
        # Log any exceptions
        logging.error(f"An error occurred: {str(e)}")
        return jsonify({'error': 'An error occurred'}), 500
    
@app.route('/conditions', methods=['GET'])
def conditionNames():
    try:

        query = """
            PREFIX schema: <https://schema.org/>
            PREFIX mesh: <https://www.ncbi.nlm.nih.gov/mesh/?term=>
            PREFIX drug: <https://drugcentral.org/drugcard/>
            PREFIX file: <https://clinicaltrials.gov/ct2/show/>

            SELECT DISTINCT ?conditionName
            WHERE {
            ?study a schema:MedicalStudy ;
                    schema:MedicalCondition ?conditionName .
            }
            """

        payload = {'query': query}

        # Set the headers
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        # Make the POST request
        response = requests.post(endpoint, data=payload, headers=headers)

        if response.status_code == 200:
            result = response.json()
            # Return JSON response
            return jsonify(result)
        else:
            return jsonify({'error': 'Failed to get a valid response'}), 500

    except Exception as e:
        # Log any exceptions
        logging.error(f"An error occurred: {str(e)}")
        return jsonify({'error': 'An error occurred'}), 500



@app.route('/submit', methods=['POST'])
def submit():
    try:
        # Extract data from the request
        data = request.data
        args = json.loads(data)

        sparql_query = queryBuilder(args)

        payload = {'query': sparql_query}

        # Set the headers
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        # Make the POST request
        response = requests.post(endpoint, data=payload, headers=headers)

        result = response.json() if response.status_code == 200 else {'error': 'Failed to get a valid response'}

        # Return JSON response
        return jsonify(result)

    except Exception as e:
        # Log any exceptions
        logging.error(f"An error occurred: {str(e)}")
        return jsonify({'error': 'An error occurred'})


def queryBuilder(args):
    query_type = args.get('type_of_request')

    prefix = """
        PREFIX schema: <https://schema.org/>
        PREFIX mesh: <https://www.ncbi.nlm.nih.gov/mesh/?term=>
        PREFIX drug: <https://drugcentral.org/drugcard/>
        PREFIX file: <https://clinicaltrials.gov/ct2/show/>
    """
    object = args.get('object').lower()
    num_results = args.get('num_res')

    if query_type == 'Mdrug_cond':
        query = f"""
            {prefix}
            SELECT ?drugName ?drug (COUNT(?drug) AS ?usageCount)
            WHERE {{
                ?study schema:MedicalCondition "{object}" .
                ?drug schema:study ?study .
                ?drug schema:name ?drugName .
            }}
            GROUP BY ?drugName ?drug
            ORDER BY DESC(?usageCount)
            LIMIT {num_results}
        """
    elif query_type == 'drug_cond':
        query = f"""
            {prefix}
            SELECT DISTINCT ?drugName ?drug
            WHERE {{
                ?study schema:MedicalCondition "{object}" .
                ?drug schema:study ?study .
                ?drug schema:name ?drugName .
            }}
            LIMIT {num_results}
        """
    elif query_type == 'Pstud_drug':
        phase = args.get('phase').lower()
        query = f"""
            {prefix}
            SELECT ?studyTitle ?study
            WHERE {{
                ?study schema:phase "{phase}" .
                ?drug schema:name "{object}" .
                ?drug schema:study ?study .
                ?study schema:title ?studyTitle .
            }}
            LIMIT {num_results}
        """
    elif query_type == 'Pstud_cond':
        phase = args.get('phase').lower()
        query = f"""
            {prefix}
            SELECT ?title ?study 
            WHERE {{
            ?study a schema:MedicalStudy ;
                    schema:phase "{phase}" ;
                    schema:MedicalCondition "{object}" ;
                    schema:title ?title .
            }}
            LIMIT {num_results}
        """
    elif query_type == 'stud_drug':
        query = f"""
            {prefix}
            SELECT DISTINCT ?studyTitle ?study
            WHERE {{
                ?drug schema:name "{object}" .
                ?drug schema:study ?study .
                ?study schema:title ?studyTitle .
            }}
            LIMIT {num_results}
        """
    elif query_type == 'stud_cond':
        query = f"""
            {prefix}
            SELECT ?title ?study 
            WHERE {{
                ?study a schema:MedicalStudy ;
                        schema:MedicalCondition "{object}" ;
                        schema:title ?title .
            }}
            LIMIT {num_results}
        """
    else:
        return None

    # Log the generated query
    # logging.info(f"Generated SPARQL query: {query}")

    return query


if __name__ == '__main__':
    app.run(debug=True)
