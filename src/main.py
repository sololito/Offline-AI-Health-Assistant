# /src/main.py

from assistant import HealthAssistant

def main():
    print("=== Offline AI Health Assistant ===\n")
    print("Enter your symptoms one by one. Type 'done' when finished.\n")

    user_symptoms = []
    while True:
        symptom = input("Enter a symptom: ").strip()
        if symptom.lower() == "done":
            break
        if symptom:
            user_symptoms.append(symptom)

    if not user_symptoms:
        print("\n⚠️  No symptoms entered. Exiting.")
        return

    assistant = HealthAssistant()
    results = assistant.diagnose(user_symptoms)

    print("\nTop Matches:")
    for idx, result in enumerate(results, 1):
        print(f"{idx}. {result['disease']} (Score: {result['match_score']}, Matches: {result['matching_symptoms']})")

if __name__ == "__main__":
    main()
