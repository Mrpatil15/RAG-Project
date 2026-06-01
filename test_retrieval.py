import os
import glob

def local_search(query):
    files = glob.glob("./data/locality_briefs/*.md")
    query_words = [w.lower() for w in query.split() if len(w) > 2]
    
    results = []
    for f_path in files:
        file_name = os.path.basename(f_path)
        with open(f_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Score based on keyword matches
        score = 0
        for word in query_words:
            score += content.lower().count(word) * 2
            # Extra points for matching in the title
            if word in file_name.lower():
                score += 10
                
        if score > 0:
            # Find the paragraph that contains the query words to show a good snippet
            paragraphs = content.split("\n\n")
            best_paragraph = ""
            best_p_score = -1
            for p in paragraphs:
                p_score = sum(p.lower().count(w) for w in query_words)
                if p_score > best_p_score:
                    best_p_score = p_score
                    best_paragraph = p
                    
            results.append((score, file_name, best_paragraph))
            
    results.sort(key=lambda x: x[0], reverse=True)
    return results

if __name__ == "__main__":
    test_queries = [
        "What is the average 2BHK price in Kanjurmarg?",
        "Tell me about the Coastal Road in South Mumbai",
        "What is driving growth in Navi Mumbai?"
    ]
    
    print("="*60)
    print("      MOCK RETRIEVAL TEST ON MUMBAI KNOWLEDGE BASE")
    print("="*60)
    
    for q in test_queries:
        print(f"\nUser Query: \"{q}\"")
        matches = local_search(q)
        if matches:
            top_score, file_name, text = matches[0]
            print(f"Retrieved Source: {file_name} (Match Score: {top_score})")
            print(f"Content:\n{text.strip()}")
        else:
            print("No relevant documents found.")
        print("-" * 60)
