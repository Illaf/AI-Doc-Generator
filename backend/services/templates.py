# services/templates.py
import markdown
TEMPLATES = {
    "minimal": """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Documentation</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            line-height: 1.6;
            color: #333;
            background: #fff;
            padding: 2rem;
            max-width: 900px;
            margin: 0 auto;
        }
        
        h1 {
            font-size: 2.5rem;
            margin-bottom: 2rem;
            font-weight: 600;
            color: #000;
        }
        
        h2 {
            font-size: 1.5rem;
            margin: 2.5rem 0 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid #e5e5e5;
            color: #111;
            font-weight: 500;
        }
        
        p {
            margin-bottom: 1rem;
            color: #555;
        }
        
        code {
            background: #f5f5f5;
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 0.9em;
        }
        
        pre {
            background: #f8f8f8;
            padding: 1rem;
            border-radius: 6px;
            overflow-x: auto;
            border-left: 3px solid #ddd;
        }
        
        .file-path {
            color: #666;
            font-size: 0.9em;
            font-family: monospace;
        }
    </style>
</head>
<body>
    {content}
</body>
</html>
""",
    
    "dark": """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Documentation</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'SF Mono', 'Monaco', 'Courier New', monospace;
            line-height: 1.7;
            color: #c9d1d9;
            background: #0d1117;
            padding: 2rem;
            max-width: 1000px;
            margin: 0 auto;
        }
        
        h1 {
            font-size: 2.5rem;
            margin-bottom: 2rem;
            font-weight: 700;
            color: #58a6ff;
            text-shadow: 0 0 20px rgba(88, 166, 255, 0.3);
        }
        
        h2 {
            font-size: 1.4rem;
            margin: 2.5rem 0 1rem;
            padding: 0.8rem;
            background: rgba(88, 166, 255, 0.1);
            border-left: 4px solid #58a6ff;
            color: #58a6ff;
            font-weight: 600;
        }
        
        p {
            margin-bottom: 1rem;
            color: #8b949e;
        }
        
        code {
            background: #161b22;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            color: #79c0ff;
            border: 1px solid #30363d;
        }
        
        pre {
            background: #161b22;
            padding: 1.2rem;
            border-radius: 8px;
            overflow-x: auto;
            border: 1px solid #30363d;
            box-shadow: 0 0 15px rgba(0, 0, 0, 0.5);
        }
        
        .file-path {
            color: #7ee787;
            font-size: 0.95em;
        }
        
        ::selection {
            background: rgba(88, 166, 255, 0.3);
        }
    </style>
</head>
<body>
    {content}
</body>
</html>
""",
    
    "notion": """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Documentation</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            line-height: 1.7;
            color: #37352f;
            background: #f7f6f3;
            padding: 3rem 2rem;
            max-width: 900px;
            margin: 0 auto;
        }
        
        h1 {
            font-size: 2.8rem;
            margin-bottom: 2.5rem;
            font-weight: 700;
            color: #37352f;
        }
        
        h2 {
            font-size: 1.6rem;
            margin: 2rem 0 1rem;
            padding: 1rem;
            background: #fff;
            border-radius: 8px;
            color: #37352f;
            font-weight: 600;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }
        
        p {
            margin-bottom: 1rem;
            color: #37352f;
        }
        
        code {
            background: #f1f1ef;
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            font-family: 'Monaco', monospace;
            font-size: 0.9em;
            color: #eb5757;
        }
        
        pre {
            background: #fff;
            padding: 1.2rem;
            border-radius: 8px;
            overflow-x: auto;
            border: 1px solid #e3e2e0;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }
        
        .file-path {
            color: #787774;
            font-size: 0.9em;
            font-family: monospace;
        }
    </style>
</head>
<body>
    {content}
</body>
</html>
""",
    
    "gradient": """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Documentation</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, sans-serif;
            line-height: 1.7;
            color: #1a1a1a;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            min-height: 100vh;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 3rem;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }
        
        h1 {
            font-size: 3rem;
            margin-bottom: 2rem;
            font-weight: 800;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        h2 {
            font-size: 1.6rem;
            margin: 2.5rem 0 1rem;
            padding: 1rem;
            background: linear-gradient(135deg, #667eea15, #764ba215);
            border-radius: 12px;
            color: #764ba2;
            font-weight: 700;
            border-left: 4px solid #667eea;
        }
        
        p {
            margin-bottom: 1rem;
            color: #333;
        }
        
        code {
            background: #f5f3ff;
            padding: 0.2rem 0.5rem;
            border-radius: 6px;
            font-family: 'Fira Code', monospace;
            color: #764ba2;
            font-size: 0.9em;
        }
        
        pre {
            background: #f8f7ff;
            padding: 1.2rem;
            border-radius: 12px;
            overflow-x: auto;
            border: 2px solid #e9e7ff;
        }
        
        .file-path {
            color: #667eea;
            font-weight: 600;
            font-size: 0.95em;
        }
    </style>
</head>
<body>
    <div class="container">
        {content}
    </div>
</body>
</html>
""",
    
    "terminal": """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Documentation</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Courier New', 'Monaco', monospace;
            line-height: 1.6;
            color: #00ff00;
            background: #000;
            padding: 2rem;
            max-width: 1000px;
            margin: 0 auto;
        }
        
        h1 {
            font-size: 2rem;
            margin-bottom: 2rem;
            font-weight: 700;
            color: #00ff00;
            border: 2px solid #00ff00;
            padding: 1rem;
            text-align: center;
        }
        
        h1::before {
            content: '> ';
        }
        
        h2 {
            font-size: 1.3rem;
            margin: 2rem 0 1rem;
            padding: 0.5rem;
            color: #00ff00;
            font-weight: 600;
            border-bottom: 1px dashed #00ff00;
        }
        
        h2::before {
            content: '$ ';
            color: #ffff00;
        }
        
        p {
            margin-bottom: 1rem;
            color: #00ff00;
        }
        
        code {
            background: #001a00;
            padding: 0.2rem 0.5rem;
            border: 1px solid #003300;
            color: #ffff00;
        }
        
        pre {
            background: #001a00;
            padding: 1rem;
            overflow-x: auto;
            border: 1px solid #003300;
            margin: 1rem 0;
        }
        
        .file-path {
            color: #00ffff;
            font-weight: bold;
        }
        
        .file-path::before {
            content: '📁 ';
        }
    </style>
</head>
<body>
    {content}
</body>
</html>
""",

    "gitbook": """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Documentation</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            line-height: 1.7;
            color: #2e3440;
            background: #fff;
            display: grid;
            grid-template-columns: 250px 1fr;
            min-height: 100vh;
        }
        
        .sidebar {
            background: #f7f8fa;
            padding: 2rem 1.5rem;
            border-right: 1px solid #e5e7eb;
            position: sticky;
            top: 0;
            height: 100vh;
            overflow-y: auto;
        }
        
        .content {
            padding: 3rem;
            max-width: 900px;
        }
        
        h1 {
            font-size: 2.5rem;
            margin-bottom: 2rem;
            font-weight: 600;
            color: #1a1a1a;
        }
        
        h2 {
            font-size: 1.5rem;
            margin: 2rem 0 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #3b82f6;
            color: #1a1a1a;
            font-weight: 600;
        }
        
        p {
            margin-bottom: 1rem;
            color: #4b5563;
        }
        
        code {
            background: #f1f5f9;
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            font-family: 'Monaco', monospace;
            font-size: 0.9em;
            color: #3b82f6;
        }
        
        pre {
            background: #f8fafc;
            padding: 1.2rem;
            border-radius: 8px;
            overflow-x: auto;
            border-left: 4px solid #3b82f6;
        }
        
        .file-path {
            color: #6366f1;
            font-weight: 500;
            font-size: 0.95em;
        }
    </style>
</head>
<body>
    <div class="sidebar">
        <h3 style="margin-bottom: 1rem; color: #3b82f6;">Documentation</h3>
        <p style="font-size: 0.9em; color: #6b7280;">Repository Contents</p>
    </div>
    <div class="content">
        {content}
    </div>
</body>
</html>
"""
}


def apply_template(markdown_content: str, template_name: str ) -> str:
    """
    Convert markdown to HTML and apply selected template
    """
    print("🎨 Using template:", template_name)

    html_content = markdown.markdown(
        markdown_content,
        extensions=["fenced_code", "codehilite", "tables"]
    )

    template = TEMPLATES.get(template_name, TEMPLATES["minimal"])

    # 🚀 SAFE replacement (no format())
    return template.replace("{content}", html_content)
