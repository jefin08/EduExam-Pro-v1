import json
import urllib.request
import urllib.parse
import time

def execute_via_onecompiler(code, language, stdin="", timeout=15.0):
    # Map input language names to OneCompiler identifiers and default filenames
    lang_map = {
        'python': ('python', 'main.py'),
        'c': ('c', 'main.c'),
        'cpp': ('cpp', 'main.cpp'),
        'java': ('java', 'Main.java')
    }
    lang_id, filename = lang_map.get(language.lower(), (language.lower(), 'main.txt'))
    
    # Request payload structure for OneCompiler's web execution API
    payload = {
        "properties": {
            "language": lang_id,
            "files": [
                {
                    "name": filename,
                    "content": code
                }
            ],
            "stdin": stdin
        }
    }
    
    url = "https://onecompiler.com/api/code/exec"
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method='POST'
    )
    
    try:
        start_time = time.time()
        with urllib.request.urlopen(req, timeout=timeout) as response:
            runtime = time.time() - start_time
            res_data = json.loads(response.read().decode('utf-8'))
            
            stdout_log = res_data.get('stdout', '') or ''
            stderr_log = res_data.get('stderr', '') or ''
            exception_log = res_data.get('exception', '') or ''
            
            # Combine errors
            error_msg = stderr_log or exception_log
            if isinstance(error_msg, list):
                error_msg = "\n".join(error_msg)
            if isinstance(stdout_log, list):
                stdout_log = "\n".join(stdout_log)
                
            error_msg = str(error_msg).strip()
            stdout_log = str(stdout_log)
            
            if error_msg:
                # If there are compiler details or syntax failure keywords, mark compile_error
                is_compile_err = any(term in error_msg.lower() for term in ["compile", "syntax", "error", "invalid", "gcc", "g++", "javac"]) and not "traceback" in error_msg.lower()
                
                if is_compile_err:
                    return {
                        'status': 'compile_error',
                        'stdout': stdout_log,
                        'stderr': error_msg,
                        'runtime': 0.0
                    }
                else:
                    return {
                        'status': 'runtime_error',
                        'stdout': stdout_log,
                        'stderr': error_msg,
                        'runtime': round(runtime, 3)
                    }
            
            return {
                'status': 'success',
                'stdout': stdout_log,
                'stderr': '',
                'runtime': round(runtime, 3)
            }
            
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode('utf-8')
        except Exception:
            err_body = ""
        return {
            'status': 'error',
            'stdout': '',
            'stderr': f"Online compiler HTTP Error {e.code}: {e.reason}\nDetail: {err_body}",
            'runtime': 0.0
        }
    except urllib.error.URLError as e:
        return {
            'status': 'error',
            'stdout': '',
            'stderr': f"Online compiler unreachable: {str(e.reason)}",
            'runtime': 0.0
        }
    except Exception as e:
        return {
            'status': 'error',
            'stdout': '',
            'stderr': f"Online compiler error: {str(e)}",
            'runtime': 0.0
        }

def normalize_output(s):
    """
    Strips out brackets, braces, commas, and collapses all whitespace 
    to make comparing data structures resilient to formatting mismatches.
    """
    chars_to_remove = "[](){},"
    for c in chars_to_remove:
        s = s.replace(c, " ")
    return " ".join(s.split())

def judge_code(code, language, test_cases, time_limit=1.0, memory_limit=256):
    """
    Evaluates submitted code against test cases using the online compilation engine.
    """
    results = []
    
    for idx, tc in enumerate(test_cases):
        tc_input = tc.get('input', '')
        expected_output = tc.get('output', '').strip()
        
        # Run via OneCompiler API
        res = execute_via_onecompiler(code, language, stdin=tc_input)
        
        if res['status'] == 'compile_error':
            return False, res['stderr'], []
            
        elif res['status'] == 'success':
            stdout = res['stdout'].strip()
            if stdout == expected_output:
                status = 'pass'
                err_msg = None
            elif normalize_output(stdout) == normalize_output(expected_output):
                status = 'pass'
                err_msg = None
            else:
                status = 'fail'
                err_msg = f"Expected: '{expected_output}', Got: '{stdout}'"
        else: # runtime_error, error, etc.
            status = res['status']
            err_msg = res['stderr'] or "Runtime error occurred during evaluation."
            
        results.append({
            'test_case_index': idx,
            'status': status,
            'runtime_seconds': res['runtime'],
            'error_message': err_msg
        })
        
    return True, None, results

def run_custom_code(code, language, custom_input, time_limit=2.0):
    """
    Runs the code with user's custom input using the online compilation engine.
    """
    return execute_via_onecompiler(code, language, stdin=custom_input)
