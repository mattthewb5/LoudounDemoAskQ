#!/usr/bin/env python3
"""
AI-powered crime information assistant using Claude API
Answers natural language questions about crime data for Athens-Clarke County addresses
"""

import os
from typing import Optional
from anthropic import Anthropic
from crime_analysis import analyze_crime_near_address, CrimeAnalysis


class CrimeAIAssistant:
    """AI assistant for answering questions about crime data"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the crime AI assistant

        Args:
            api_key: Anthropic API key (optional, will use env var if not provided)
        """
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. Set it as an environment variable or pass it to the constructor."
            )
        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-3-haiku-20240307"

    def _format_crime_data(self, analysis: CrimeAnalysis) -> str:
        """
        Format crime analysis into a clear text summary for Claude

        Args:
            analysis: CrimeAnalysis object

        Returns:
            Formatted string with all crime data
        """
        from datetime import datetime, timedelta

        stats = analysis.statistics
        trends = analysis.trends
        safety = analysis.safety_score

        # Calculate date range
        today = datetime.now()
        start_date = today - timedelta(days=analysis.time_period_months * 30)
        date_range = f"{start_date.strftime('%B %Y')} to {today.strftime('%B %Y')}"

        lines = []

        # Address and search parameters
        lines.append(f"ADDRESS: {analysis.address}")
        lines.append(f"Search Radius: {analysis.radius_miles} miles")
        lines.append(f"Time Period: {analysis.time_period_months} months ({date_range})")
        lines.append(f"Data Retrieved: {today.strftime('%B %d, %Y')}")
        lines.append("")

        # Overall statistics
        lines.append("OVERALL STATISTICS:")
        lines.append(f"- Total Crimes: {stats.total_crimes}")
        lines.append(f"- Crimes per Month: {stats.crimes_per_month:.1f}")
        lines.append(f"- Most Common Crime: {stats.most_common_crime} ({stats.most_common_count} incidents)")
        lines.append("")

        # Crime categories
        lines.append("CRIME BREAKDOWN BY CATEGORY:")
        lines.append(f"- Violent Crimes: {stats.violent_count} ({stats.violent_percentage}% of total)")
        lines.append(f"  Examples: Assault, robbery, homicide, kidnapping, sexual assault")
        lines.append(f"- Property Crimes: {stats.property_count} ({stats.property_percentage}% of total)")
        lines.append(f"  Examples: Burglary, larceny, theft, vandalism, fraud, forgery")
        lines.append(f"- Traffic Offenses: {stats.traffic_count} ({stats.traffic_percentage}% of total)")
        lines.append(f"  Examples: DUI, driving violations")
        lines.append(f"- Other: {stats.other_count} ({stats.other_percentage}% of total)")
        lines.append(f"  Examples: Drug violations, liquor laws, disorderly conduct, trespassing")
        lines.append("")

        # Top crimes in each category
        lines.append("TOP CRIMES BY CATEGORY:")
        for category_name, category_label in [
            ('violent', 'VIOLENT CRIMES'),
            ('property', 'PROPERTY CRIMES'),
            ('traffic', 'TRAFFIC OFFENSES'),
            ('other', 'OTHER')
        ]:
            category_crimes = analysis.category_breakdown[category_name]
            if category_crimes:
                from collections import defaultdict
                crime_counts = defaultdict(int)
                for crime in category_crimes:
                    crime_counts[crime.crime_type] += 1

                lines.append(f"{category_label}:")
                top_crimes = sorted(crime_counts.items(), key=lambda x: x[1], reverse=True)[:3]
                for crime_type, count in top_crimes:
                    lines.append(f"  - {crime_type}: {count}")
                lines.append("")

        # Trend analysis
        lines.append("CRIME TRENDS (Last 6 months vs. Previous 6 months):")
        lines.append(f"- Recent Period (last 6 months): {trends.recent_count} crimes")
        lines.append(f"- Previous Period (6-12 months ago): {trends.previous_count} crimes")
        lines.append(f"- Change: {trends.change_count:+d} crimes ({trends.change_percentage:+.1f}%)")
        lines.append(f"- Trend: {trends.trend_description}")
        lines.append("")

        # Comparison to Athens average
        if analysis.comparison:
            comp = analysis.comparison
            lines.append("COMPARISON TO ATHENS-CLARKE COUNTY AVERAGE:")
            lines.append(f"- This Area: {comp.area_crime_count} crimes")
            lines.append(f"- Athens Average: {comp.athens_average:.1f} crimes (within {analysis.radius_miles} miles)")
            lines.append(f"- Difference: {comp.difference_count:+.1f} crimes ({comp.difference_percentage:+.0f}%)")
            lines.append(f"- Assessment: {comp.relative_ranking}")
            lines.append(f"- Summary: {comp.comparison_text}")
            lines.append("")

        # Safety score
        lines.append("SAFETY SCORE:")
        lines.append(f"- Score: {safety.score} out of 5 (5 = safest)")
        lines.append(f"- Level: {safety.level}")
        lines.append(f"- Explanation: {safety.explanation}")
        lines.append("")

        # Data sources and limitations
        lines.append("DATA SOURCES AND CITATION INFORMATION:")
        lines.append(f"- Source: Athens-Clarke County Police Department")
        lines.append(f"- Access Method: ArcGIS REST API")
        lines.append(f"- Crime Map: https://accpd-public-transparency-site-athensclarke.hub.arcgis.com/pages/crime")
        lines.append(f"- Date Range: {date_range}")
        lines.append(f"- Search Area: Within {analysis.radius_miles} miles of the address")
        lines.append(f"- Data Current As Of: {today.strftime('%B %d, %Y')}")
        lines.append("")

        lines.append("IMPORTANT DATA LIMITATIONS:")
        lines.append("- Shows only REPORTED crimes that appear in public police data")
        lines.append("- Does not include all crimes (some may be unreported or excluded for privacy)")
        lines.append("- Crime locations may be approximate for privacy protection")
        lines.append("- Past crime data does not predict future crime")
        lines.append("- Crime statistics should be considered alongside other factors when evaluating a property")

        return "\n".join(lines)

    def answer_crime_question(self, address: str, question: str,
                             radius_miles: float = 0.5,
                             months_back: int = 12) -> str:
        """
        Answer a natural language question about crime near an address

        Args:
            address: Street address in Athens-Clarke County
            question: User's question about crime/safety
            radius_miles: Search radius in miles (default: 0.5)
            months_back: How many months of history (default: 12)

        Returns:
            Claude's natural language response

        Raises:
            ValueError: If address is invalid or API key is missing
            RuntimeError: If crime data cannot be retrieved
        """
        # Get crime analysis
        print(f"📊 Analyzing crime data for {address}...")
        analysis = analyze_crime_near_address(address, radius_miles, months_back)

        if not analysis:
            raise RuntimeError(
                f"Could not retrieve crime data for {address}. "
                "Please check the address is in Athens-Clarke County, GA."
            )

        # Format data for Claude
        crime_data = self._format_crime_data(analysis)

        # Create system prompt
        system_prompt = """You are a helpful and balanced real estate research assistant specializing in crime and safety information for Athens-Clarke County, Georgia.

CRITICAL INSTRUCTIONS FOR ACCURATE AND BALANCED RESPONSES:

1. REQUIRED RESPONSE FORMAT - Use this exact structure:

   Brief answer:
   - Start with a clear, direct answer to the question
   - Begin with "According to Athens-Clarke County Police data from [date range], within [radius] miles of this address..."
   - Be balanced - acknowledge both positive and negative aspects

   Supporting statistics
   - Cite specific numbers and percentages
   - Include total crimes, crimes per month, category breakdown
   - Reference the safety score (X out of 100)

   Trend information
   - State whether crime is increasing, decreasing, or stable
   - Include the specific percentage change
   - Mention the comparison period (last 6 months vs. previous 6 months)

   Data sources and limitations
   - Include: "Data current as of [today's date]"
   - Include: "View the crime map: https://accpd-public-transparency-site-athensclarke.hub.arcgis.com/pages/crime"
   - Include: "This data reflects reported crimes only; not all crimes are reported"
   - Include: "Crime statistics should be considered alongside other factors when evaluating a property"

2. CITATION REQUIREMENTS:
   - ALWAYS start with "According to Athens-Clarke County Police data from [date range]..."
   - ALWAYS specify "within [X] miles of the address"
   - Use exact numbers (e.g., "448 reported crimes", "17.2% were violent")
   - Reference the specific data source in Section 4

3. BE BALANCED AND FACT-BASED:
   - Do NOT exaggerate danger or use fear-mongering language
   - Do NOT downplay legitimate concerns
   - Present facts objectively and let the user decide
   - Acknowledge both positive and negative aspects

4. SPECIAL CASE - NO CRIMES FOUND:
   - Say: "I found no reported crimes within [X] miles in the last [Y] months"
   - Do NOT say "This is the safest place" or make speculation
   - Note: "However, this only reflects reported crimes in public police data"

5. DO NOT SPECULATE:
   - Use only the crime statistics provided
   - If the data doesn't answer the question, say so
   - Never make predictions about future crime
   - Never compare to other cities unless data is provided

6. BE HELPFUL AND PROFESSIONAL:
   - Answer the specific question asked
   - Use clear, accessible language
   - Show empathy for home buyers' legitimate concerns
   - Suggest visiting the neighborhood in person"""

        # Create user prompt
        user_prompt = f"""Please answer this question about crime and safety for a property in Athens-Clarke County, Georgia.

QUESTION: {question}

CRIME DATA:
{crime_data}

REQUIRED FORMAT FOR YOUR RESPONSE:

Brief answer:
Start with: "According to Athens-Clarke County Police data from [date range], within {radius_miles} miles of this address..."
Provide a balanced, direct answer to the question.

Supporting statistics
Use bullet points to cite specific numbers:
• Total crimes and crimes per month
• Category breakdown (violent %, property %, etc.)
• Comparison to Athens average (if provided in data - e.g., "X% more/less than Athens average")
• Safety score (X out of 100)
• Most common crime types

Trend information
State whether crime is increasing, decreasing, or stable, with the percentage change.
If comparison to Athens average is provided, mention whether this is a high or low activity area.

Data sources and limitations
Include ALL of these:
• "Data current as of [today's date from the data above]"
• "View the crime map: https://accpd-public-transparency-site-athensclarke.hub.arcgis.com/pages/crime"
• "This data reflects reported crimes only; not all crimes are reported"
• "Crime statistics should be considered alongside other factors when evaluating a property"

Remember: Be helpful, honest, and balanced. Don't exaggerate or minimize concerns. Follow the format exactly."""

        # Call Claude API
        print(f"🤖 Asking Claude AI to analyze the question...")

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ]
            )

            response = message.content[0].text
            return response

        except Exception as e:
            raise RuntimeError(f"Error calling Claude API: {str(e)}")


def main():
    """Test the crime AI assistant with sample questions"""

    # Test questions for 150 Hancock Avenue
    test_address = "150 Hancock Avenue, Athens, GA 30601"
    test_questions = [
        "How safe is this neighborhood?",
        "Should I be worried about crime here?",
        "What types of crimes happen near this address?",
        "Is crime getting better or worse?"
    ]

    print("=" * 80)
    print("CRIME AI ASSISTANT TEST")
    print("=" * 80)
    print(f"\nTesting with address: {test_address}")
    print(f"Using 0.5 mile radius, 12 months of data\n")

    # Initialize assistant
    try:
        assistant = CrimeAIAssistant()
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("\nPlease set your ANTHROPIC_API_KEY environment variable:")
        print("  export ANTHROPIC_API_KEY='your-api-key-here'")
        return

    # Test each question
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*80}")
        print(f"QUESTION {i}: {question}")
        print(f"{'='*80}\n")

        try:
            answer = assistant.answer_crime_question(
                address=test_address,
                question=question,
                radius_miles=0.5,
                months_back=12
            )

            print("ANSWER:")
            print(answer)
            print()

        except Exception as e:
            print(f"❌ Error: {e}")

        print("\n")

    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
