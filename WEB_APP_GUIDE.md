# Athens Home Buyer Research Assistant - Web Interface Guide

## Quick Start

### 1. Install Dependencies

Make sure you have all required packages installed:

```bash
pip install -r requirements.txt
pip install anthropic
pip install streamlit
```

### 2. Set Your API Key

Set your Anthropic API key as an environment variable:

**On macOS/Linux:**
```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

**On Windows (Command Prompt):**
```cmd
set ANTHROPIC_API_KEY=your-api-key-here
```

**On Windows (PowerShell):**
```powershell
$env:ANTHROPIC_API_KEY="your-api-key-here"
```

Get your API key at: https://console.anthropic.com/

### 3. Run the Web App

```bash
streamlit run streamlit_app.py
```

The app will automatically open in your default web browser at `http://localhost:8501`

## Features

- **Address Lookup**: Enter any Athens-Clarke County address
- **Natural Language Questions**: Ask questions in plain English
- **AI-Powered Answers**: Claude AI analyzes school data and provides balanced responses
- **Source Citations**: All facts are cited with data sources and years
- **Clean Interface**: Professional, easy-to-use web design
- **Verification Links**: Direct links to original data sources

## Usage

1. **Enter an Address**: Type a street address in Athens-Clarke County, GA
   - Example: `150 Hancock Avenue, Athens, GA 30601`

2. **Ask a Question**: Type your question about the schools
   - Example: `How good are the schools at this address?`
   - Example: `What are the test scores?`
   - Example: `Tell me about school quality`

3. **Click Search**: The AI will analyze the data and provide a comprehensive answer with citations

4. **Explore More**:
   - View school assignments (Elementary, Middle, High)
   - See complete raw data
   - Verify sources with provided links

## Example Questions

- What are the test scores at this address?
- How good are the schools?
- Tell me about school quality for this property
- What's the graduation rate at the high school?
- What are the demographics of these schools?
- Are the schools improving or declining?
- How does this school compare to others?

## Troubleshooting

**"Address not found"**
- Make sure the address is in Athens-Clarke County, GA
- Try different street abbreviations (St vs Street, Ave vs Avenue)
- Check for typos in the street name

**"API key required"**
- Make sure you've set the ANTHROPIC_API_KEY environment variable
- Restart the terminal after setting the environment variable
- Verify your API key is valid at https://console.anthropic.com/

**"Streamlit not found"**
- Run `pip install streamlit` to install Streamlit
- Make sure you're using the correct Python environment

## Data Sources

- **School Assignments**: Clarke County Schools Street Index (2024-25)
- **Performance Data**: Georgia Governor's Office of Student Achievement (2023-24)

## Important Notes

⚠️ **Disclaimer**:
- School attendance zones can change year-to-year
- Performance data is from the 2023-24 school year
- Always verify school assignments with Clarke County School District
- This tool is for research and informational purposes only
- Not affiliated with Clarke County School District or Georgia Department of Education

## Technical Details

- **Framework**: Streamlit
- **AI Model**: Claude 3 Haiku (via Anthropic API)
- **Data**: 1,957 street entries, 22 schools with performance data
- **Coverage**: All of Athens-Clarke County, GA

## Alternative Interfaces

If you prefer command-line interfaces:

- **Standard CLI**: `python3 school_lookup_cli.py`
- **AI-Powered CLI**: `python3 school_lookup_ai_cli.py`
- **Basic Lookup**: `python3 school_info.py "address"`

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the main README.md for more details
3. Verify your data sources are up-to-date

---

**Enjoy researching Athens schools!** 🏡📚
