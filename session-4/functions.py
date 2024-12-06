from bs4 import BeautifulSoup
import torch

def parse_html_content(html_content):
    """
    Parse HTML content and extract structured content with sections and paragraphs.
    
    Args:
        html_content (str): Raw HTML content to parse
        
    Returns:
        list: List of dictionaries containing structured content
    """
    # Parse HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Get article title
    article_title = soup.find('title').get_text().strip() if soup.find('title') else "Untitled"
    
    # Initialize variables
    structured_content = []
    current_section = "Main"  # Default section if no headers found
    
    # Find all headers and text content
    content_elements = soup.find_all(['h1', 'h2', 'h3', 'p', 'ul', 'ol'])
    
    for element in content_elements:
        if element.name in ['h1', 'h2', 'h3']:
            current_section = element.get_text().strip()
        elif element.name in ['p', 'ul', 'ol']:
            text = element.get_text().strip()
            # Only add non-empty content that's at least 30 characters long
            if text and len(text) >= 30:
                structured_content.append({
                    'article_title': article_title,
                    'section': current_section,
                    'text': text
                })
    
    return structured_content


def get_top_k_items(similarities, chunk_list, temp=0.1, k=3, threshold=0.05):
    """
    Retrieves the top-k most similar items from a list based on a similarity matrix.
    
    Args:
        similarities (torch.Tensor): A 2D tensor where each row represents the similarity scores of an item.
        chunk_list (list): A list of content items corresponding to the columns of the similarity tensor.
        temp (float, optional): Temperature for softmax rescaling. Defaults to 0.1.
        k (int, optional): Number of top items to return. Defaults to 3.
        threshold (float, optional): Minimum similarity score for inclusion. Defaults to 0.05.
    
    Returns:
        list: The top-k most similar content items.
        list: The scores corresponding to the top-k items.
    """
    # Rescale similarities via softmax
    scores = torch.nn.functional.softmax(similarities / temp, dim=1)

    # Get sorted indices and scores
    sorted_indices = scores.argsort(descending=True)[0]
    sorted_scores = scores[0][sorted_indices]

    # Filter by threshold and get top k
    filtered_indices = [
        idx.item() for idx, score in zip(sorted_indices, sorted_scores) 
        if score.item() >= threshold
    ][:k]

    # Get corresponding content items and scores
    top_results = [chunk_list[i] for i in filtered_indices]
    result_scores = [scores[0][i].item() for i in filtered_indices]

    return top_results, result_scores

def compute_query_similarities(query, model, chunk_embeddings):
    """
    Computes similarity scores between a query and a list of chunk embeddings.

    Args:
        query (str): The query string to compute similarities for.
        model: The embedding model that provides methods for encoding and similarity computation.
        chunk_embeddings (torch.Tensor): A tensor containing embeddings for the content chunks.

    Returns:
        torch.Tensor: A tensor of similarity scores between the query and the content chunks.
    """
    # Encode the query into an embedding
    query_embedding = model.encode(query)
    
    # Compute similarity between query embedding and all chunk embeddings
    similarities = model.similarity(query_embedding, chunk_embeddings)
    
    return similarities

def format_results_to_markdown(top_results):
    """
    Formats a list of result dictionaries into a Markdown string for display.

    Args:
        top_results (list): A list of dictionaries, each containing 'article_title', 'section', and 'text' keys.

    Returns:
        str: A formatted Markdown string containing the titles, sections, and snippets from the results.
    """
    results_markdown = ""
    for i, result in enumerate(top_results, start=1):
        results_markdown += f"{i}. **Article title:** {result['article_title']}  \n"
        results_markdown += f"   **Section:** {result['section']}  \n"
        results_markdown += f"   **Snippet:** {result['text']}  \n\n"
    
    return results_markdown

def semantic_search(query, model, chunk_embeddings, chunk_list, temp=0.1, k=3, threshold=0.05):
    """
    Executes a semantic search pipeline: computes similarities, retrieves top results, and formats them into Markdown.

    Args:
        query (str): The search query string.
        model: The embedding model with methods for encoding and similarity computation.
        chunk_embeddings (torch.Tensor): A tensor of precomputed chunk embeddings.
        chunk_list (list): A list of content chunks corresponding to the embeddings.
        temp (float, optional): Temperature for softmax rescaling. Defaults to 0.1.
        k (int, optional): Number of top items to return. Defaults to 3.
        threshold (float, optional): Minimum similarity score for inclusion. Defaults to 0.05.

    Returns:
        str: Formatted Markdown string of the top results.
    """
    # Compute similarities between the query and chunk embeddings
    similarities = compute_query_similarities(query, model, chunk_embeddings)
    
    # Retrieve the top-k results and their scores
    top_results, result_scores = get_top_k_items(similarities, chunk_list, temp=temp, k=k, threshold=threshold)
    
    # Format the top results into a Markdown string
    results_markdown = format_results_to_markdown(top_results)
    
    return results_markdown

def answer_query(query, results_markdown, prompt_template, client):
    """
        Function answer user query based on semantic search results
    """
    prompt = prompt_template(query, results_markdown)
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ], 
        temperature = 0.5,
    )
    
    # extract response
    return response.choices[0].message.content