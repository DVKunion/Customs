import json
import requests
import common.timer


class GraphQL:
    def __init__(self, github_token, date="", batch_size=100):
        self.count = 0
        self.url = 'https://api.github.com/graphql'
        self.batch_size = batch_size
        self.token = github_token
        self.query_time = common.timer.get_previous_day()
        if date != "":
            self.query_time = date
        self.query = f'''language:Dockerfile created:{self.query_time}'''
        self.repos = []

    def fetch_all_result(self):
        data = self.run_graphql_query(count_query(self.query))
        count = data["data"]['search']['repositoryCount']
        self.count = count
        if count <= 1000:
            self.fetch_results_batch("")

    def fetch_results_batch(self, after):
        data = self.run_graphql_query(query(self.query, self.batch_size, after))
        try:
            rateLimit = data["data"]["rateLimit"]
            nodes = data["data"]["search"]["nodes"]
            page_info = data["data"]["search"]["pageInfo"]
            self.repos.extend(nodes)

            print("rate limit:", rateLimit)
            print("page info:", page_info)
            if page_info["hasNextPage"]:
                self.fetch_results_batch(page_info["endCursor"])
        except:
            print(json.dumps(data))

    def run_graphql_query(self, body):
        response = requests.post(self.url, json={'query': body}, headers={'Authorization': f'Bearer {self.token}'})
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"GraphQL query failed with status code: {response.status_code}\n{response.text}")


def count_query(search_query):
    return f'''
    query{{
      search(query: "{search_query}", type: REPOSITORY, first: 1) {{
        repositoryCount
      }}
    }}
    '''


def query(search_query, first, after):
    param = f'''query: "{search_query}", type: REPOSITORY,first: {first}, after:"{after}" '''
    if after == "":
        param = f'''query: "{search_query}", type: REPOSITORY, first: {first}'''
    return f'''
    query {{
      rateLimit {{
        limit
        cost
        remaining
        used
        resetAt
        nodeCount
      }}
      search({param}) {{
        nodes {{
          ... on Repository {{
            nameWithOwner
            description
            url
            createdAt
            stargazerCount
            forkCount
          }}
        }}
        pageInfo {{
          endCursor
          hasNextPage
        }}
      }}
    }}
'''
