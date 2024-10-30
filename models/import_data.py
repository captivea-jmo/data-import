from odoo import models, api
import pandas as pd
import json
import requests
from odoo.exceptions import UserError
import time
import gc


class ImportData(models.TransientModel):
    _name = 'import.data'
    _description = 'Import Data from XLSX'

    @api.model
    def import_from_xlsx(self, file_path, model_name, username, password):
        start_time = time.time()  # Démarrer le chronomètre
        try:
            # Lire le fichier Excel
            df = pd.read_excel(file_path)

            # Récupérer la liste des champs du modèle cible
            model_fields = self.env[model_name].fields_get().keys()

            for column in df.columns:
                if '/id' in column:
                    df[column.replace('/id','')] = df[column].apply(self._get_internal_id)
                    df = df.drop(columns=column)

            df = df[[col for col in df.columns if col in model_fields and "noimport" not in col.lower()]]
            data = df.to_dict(orient='records')

            # Paramètres de connexion
            url = self.env['ir.config_parameter'].sudo().get_param('web.base.url') + '/jsonrpc'
            db = self.env.cr.dbname

            # Authentification JSON-RPC pour obtenir le UID
            auth_response = requests.post(url, json={
                'jsonrpc': '2.0',
                'method': 'call',
                'params': {
                    'service': 'common',
                    'method': 'login',
                    'args': [db, username, password],
                },
                'id': 1,
            })

            # Vérifier l'authentification
            if auth_response.status_code != 200 or 'result' not in auth_response.json():
                return False, "Erreur d'authentification"

            uid = auth_response.json()['result']

            # Importation des données par lots
            chunk_size = 100
            for i in range(0, len(data), chunk_size):
                chunk = data[i:i + chunk_size]

                response = requests.post(url, json={
                    'jsonrpc': '2.0',
                    'method': 'call',
                    'params': {
                        'service': 'object',
                        'method': 'execute_kw',
                        'args': [db, uid, password, model_name, 'create', [chunk]],
                    },
                    'id': i,
                })

                if response.status_code != 200 or 'error' in response.json():
                    return False, f"Erreur d'importation pour le bloc {i}: {response.json()}"

                    # Libérer la mémoire après chaque chunk
                    del chunk
                    gc.collect()

            # Calcul du temps total d'importation
            end_time = time.time()
            total_time = end_time - start_time

            return True, f"Importation réussie en {total_time:.2f} secondes."
        except Exception as e:
            return False, str(e)

    def _get_internal_id(self, external_id):
        try:
            object = self.env.ref(external_id)
            return object.id
        except ValueError:
            raise UserError(f"Objet avec ID externe '{external_id}' introuvable.")
