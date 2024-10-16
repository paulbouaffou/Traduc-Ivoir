import sys
from flask import Flask, render_template, request
from SPARQLWrapper import SPARQLWrapper, JSON

app = Flask(__name__)

# Endpoint URL pour interroger Wikidata via SPARQL
endpoint_url = "https://query.wikidata.org/sparql"

# Variables pour stocker les statistiques
stats = {
    'total_articles': 0,
    'translated_articles': {},
    'events': []
}

# Requête SPARQL pour récupérer les articles liés à la Côte d'Ivoire
def build_query():
    query = """
    SELECT ?item ?itemLabel ?article_en ?article_de ?article_es ?article_ar ?article_it
    WHERE {
        ?item wdt:P17 wd:Q1008.  # Q1008 est le code Wikidata pour la Côte d'Ivoire

        OPTIONAL { ?article_en schema:about ?item; schema:isPartOf <https://en.wikipedia.org/>. }
        OPTIONAL { ?article_de schema:about ?item; schema:isPartOf <https://de.wikipedia.org/>. }
        OPTIONAL { ?article_es schema:about ?item; schema:isPartOf <https://es.wikipedia.org/>. }
        OPTIONAL { ?article_ar schema:about ?item; schema:isPartOf <https://ar.wikipedia.org/>. }
        OPTIONAL { ?article_it schema:about ?item; schema:isPartOf <https://it.wikipedia.org/>. }

        FILTER NOT EXISTS { ?article_fr schema:about ?item; schema:isPartOf <https://fr.wikipedia.org/>. }

        SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
    }
    """
    return query

# Fonction pour obtenir les résultats via SPARQLWrapper
def get_results(endpoint_url, query):
    user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()

# Fonction pour extraire l'ID Wikidata (QXXXXX)
def get_wikidata_id(item_uri):
    return item_uri.split('/')[-1]

# Fonction pour extraire le titre de l'article Wikipédia
def get_article_title(article_url):
    return article_url.split('/')[-1].replace('_', ' ')

# Route principale qui affiche les articles en fonction de la langue sélectionnée
@app.route('/', methods=['GET', 'POST'])
def index():
    articles = []
    lang = ''
    if request.method == 'POST':
        lang = request.form.get('langue')

        # Requête SPARQL
        query = build_query()
        results = get_results(endpoint_url, query)

        # Filtrer les articles par langue sélectionnée
        for result in results["results"]["bindings"]:
            article_url = result.get(f'article_{lang}', {}).get('value')
            if article_url:
                # Extraire l'ID Wikidata et le titre de l'article
                wikidata_id = get_wikidata_id(result['item']['value'])
                article_title = get_article_title(article_url)

                articles.append({
                    'wikidata_id': wikidata_id,
                    'label': result['itemLabel']['value'],
                    'url': article_url,
                    'article_title': article_title  # Titre extrait
                })

                # Mise à jour des statistiques
                if lang not in stats['translated_articles']:
                    stats['translated_articles'][lang] = 0
                stats['translated_articles'][lang] += 1

            # Mise à jour des statistiques d'événements
            stats['total_articles'] += len(articles)

    return render_template('index.html', articles=articles, lang=lang)


# Lancer l'application
if __name__ == '__main__':
    app.run(debug=True)
