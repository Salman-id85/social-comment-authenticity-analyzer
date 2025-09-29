# Comment Checker 

**Comment Checker** is a Python-based tool that analyzes the authenticity of social media comments across platforms like **YouTube, Facebook, Instagram, X (Twitter), LinkedIn**, and also from CSV inputs.  
It applies **heuristic rules** (not heavy ML) to detect spammy or inauthentic patterns and generates a **PDF report** with detailed analysis and a pie chart visualization.

---

## Features
- Multi-platform support: YouTube, Facebook, Instagram, X (Twitter), LinkedIn
- CSV file input support
- Heuristic-based scoring for authenticity
- PDF reports with:
  - Pie chart breakdown
  - Detailed comment-wise analysis
- Works even without API keys (demo mode included)

---

## Project Structure

comment_checker.py # Main tool
requirements.txt # Python dependencies
newconfer.pdf # Research paper about this tool

## Installation
Clone the repo:
```bash
git clone https://github.com/your-username/comment-checker.git
cd comment-checker
```
Install dependencies:
```bash
pip install -r requirements.txt
```
## Usage
Run the tool:
```bash
python comment_checker.py
```
Choose from the interactive menu:
- CSV file
- YouTube URL
- Facebook/Instagram/X/LinkedIn URL

## Example Output
- Pie Chart of authenticity distribution
- PDF Report with:
   - Comment-by-comment analysis
   - Heuristic reasoning
## Research Paper
For detailed methodology and results, see:
confercepaper.pdf()

##License

MIT License – free to use, modify, and distribute.

## Author
Salman S
B.E. Computer Science and Engineering
C Abdul Hakeem College of Engineering and Technology, Tamil Nadu, India

---

##  License
Use **MIT License** for maximum openness.

---

### 6. Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit: Comment Checker tool and paper"
git branch -M main
git remote add origin https://github.com/your-username/comment-checker.git
git push -u origin main
```
