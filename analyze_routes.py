import ast
import os
import json
import re

route_dir = 'app/routes'
results = []

for root, dirs, files in os.walk(route_dir):
    for fname in sorted(files):
        if fname.endswith('.py'):
            fpath = os.path.join(root, fname).replace('\', '/')
            try:
                with open(os.path.join(root, fname), 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 使用正则表达式提取蓝图和路由信息
                blueprints = re.findall(r'(\w+)\s*=\s*Blueprint\s*\(', content)
                routes = re.findall(r'@\w+\.route\s*\([\'"](\/[^\'"]+)', content)
                route_funcs = re.findall(r'def\s+(\w+)\s*\(\s*', content)
                
                # 获取路由装饰器后的函数名
                route_functions = []
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if '@' in line and 'route' in line:
                        # 查找函数定义
                        for j in range(i+1, min(i+5, len(lines))):
                            if lines[j].strip().startswith('def '):
                                func_name = lines[j].strip().split('def ')[1].split('(')[0].strip()
                                route_functions.append(func_name)
                                break
                
                results.append({
                    'file': fpath,
                    'blueprints': blueprints if blueprints else ['unknown'],
                    'route_count': len(route_functions),
                    'routes': route_functions[:15]
                })
            except Exception as e:
                results.append({
                    'file': fpath,
                    'error': str(e)
                })

print(json.dumps(results, ensure_ascii=False, indent=2))
