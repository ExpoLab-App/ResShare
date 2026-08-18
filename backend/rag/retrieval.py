from backend.rag.vector_store import get_vector_store


def search(username: str, query: str, top_k: int = 5) -> list:
    """
    Search for relevant documents using the RAG manager.

    Args:
        username (str): The username of the user.
        query (str): The search query.
        top_k (int): The number of top results to return.

    Returns:
        list: A list of relevant documents.
    """
    #surely there is a better way to do this than creating a new instance every time
    vector_store = get_vector_store()
    
    return vector_store.search_user_vector_db(username, query, top_k)