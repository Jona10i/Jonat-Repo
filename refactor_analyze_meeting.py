#!/usr/bin/env python3
"""Refactor analyze_meeting method to reduce cognitive complexity"""

with open('meeting_assistant_ios26.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the analyze_meeting method and replace it with refactored version
old_method = '''    def analyze_meeting(self, transcript):
        """Analyze meeting transcript for insights"""
        analysis = {
            "action_items": [],
            "decisions": [],
            "topics": [],
            "sentiment": None,
            "summary": None,
            "participants": []
        }

        if not transcript or not NLP_AVAILABLE:
            return analysis

        try:
            doc = self.nlp(transcript)
            action_keywords = ["need to", "should", "will", "must", "going to", "plan to", "follow up"]
            for sent in doc.sents:
                sent_text = sent.text.lower()
                if any(keyword in sent_text for keyword in action_keywords):
                    if "?" not in sent.text:
                        analysis["action_items"].append(sent.text.strip())

            decision_keywords = ["decided", "agreed", "conclusion", "resolved", "approved"]
            for sent in doc.sents:
                sent_text = sent.text.lower()
                if any(keyword in sent_text for keyword in decision_keywords):
                    analysis["decisions"].append(sent.text.strip())

            topics = set()
            for ent in doc.ents:
                if ent.label_ in ["ORG", "PRODUCT", "EVENT", "GPE", "WORK_OF_ART"]:
                    topics.add(ent.text)
            for chunk in doc.noun_chunks:
                if len(chunk.text) > 3:
                    topics.add(chunk.text)
            analysis["topics"] = list(topics)[:10]

            chunks = [transcript[i:i+512] for i in range(0, len(transcript), 512)]
            sentiments = []
            for chunk in chunks[:5]:
                result = self.sentiment_analyzer(chunk[:512])[0]
                sentiments.append(result['label'])
            analysis["sentiment"] = max(set(sentiments), key=sentiments.count) if sentiments else "NEUTRAL"

            if len(transcript) > 100:
                summary_input = transcript[:1024]
                summary = self.summarizer(summary_input, max_length=150, min_length=30, do_sample=False)
                analysis["summary"] = summary[0]['summary_text']

            names = set()
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    names.add(ent.text)
            analysis["participants"] = list(names)[:10]

        except Exception as e:
            self.logger.error(f"Analysis error: {e}")

        return analysis'''

new_method = '''    def _extract_action_items(self, doc):
        """Extract action items from the document."""
        action_items = []
        action_keywords = ["need to", "should", "will", "must", "going to", "plan to", "follow up"]
        for sent in doc.sents:
            sent_text = sent.text.lower()
            if any(keyword in sent_text for keyword in action_keywords):
                if "?" not in sent.text:
                    action_items.append(sent.text.strip())
        return action_items

    def _extract_decisions(self, doc):
        """Extract decisions from the document."""
        decisions = []
        decision_keywords = ["decided", "agreed", "conclusion", "resolved", "approved"]
        for sent in doc.sents:
            sent_text = sent.text.lower()
            if any(keyword in sent_text for keyword in decision_keywords):
                decisions.append(sent.text.strip())
        return decisions

    def _extract_topics(self, doc):
        """Extract topics from the document."""
        topics = set()
        for ent in doc.ents:
            if ent.label_ in ["ORG", "PRODUCT", "EVENT", "GPE", "WORK_OF_ART"]:
                topics.add(ent.text)
        for chunk in doc.noun_chunks:
            if len(chunk.text) > 3:
                topics.add(chunk.text)
        return list(topics)[:10]

    def _analyze_sentiment(self, transcript):
        """Analyze sentiment of the transcript."""
        chunks = [transcript[i:i+512] for i in range(0, len(transcript), 512)]
        sentiments = []
        for chunk in chunks[:5]:
            result = self.sentiment_analyzer(chunk[:512])[0]
            sentiments.append(result['label'])
        return max(set(sentiments), key=sentiments.count) if sentiments else "NEUTRAL"

    def _generate_summary(self, transcript):
        """Generate summary of the transcript."""
        if len(transcript) > 100:
            summary_input = transcript[:1024]
            summary = self.summarizer(summary_input, max_length=150, min_length=30, do_sample=False)
            return summary[0]['summary_text']
        return None

    def _extract_participants(self, doc):
        """Extract participant names from the document."""
        names = set()
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                names.add(ent.text)
        return list(names)[:10]

    def analyze_meeting(self, transcript):
        """Analyze meeting transcript for insights"""
        analysis = {
            "action_items": [],
            "decisions": [],
            "topics": [],
            "sentiment": None,
            "summary": None,
            "participants": []
        }

        if not transcript or not NLP_AVAILABLE:
            return analysis

        try:
            doc = self.nlp(transcript)
            analysis["action_items"] = self._extract_action_items(doc)
            analysis["decisions"] = self._extract_decisions(doc)
            analysis["topics"] = self._extract_topics(doc)
            analysis["sentiment"] = self._analyze_sentiment(transcript)
            analysis["summary"] = self._generate_summary(transcript)
            analysis["participants"] = self._extract_participants(doc)
        except Exception as e:
            self.logger.error(f"Analysis error: {e}")

        return analysis'''

content = content.replace(old_method, new_method)

with open('meeting_assistant_ios26.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("analyze_meeting method refactored successfully!")
