"""Catalog, square crop and selection using installation-owned raster images."""
from pathlib import Path
import hashlib
import io
import json
import math
import re
from PIL import Image,ImageOps
from .. import storage


def contained(root,name):
    root=Path(root).resolve();path=root/name
    if Path(name).is_absolute() or not path.resolve().is_relative_to(root):raise ValueError('catalog_relative_file')
    for part in [path,*path.parents]:
        if part==root:break
        if part.is_symlink():raise ValueError('regular_catalog_file')
    return path


def catalog(root):
    rows=json.loads(contained(root,'catalog.json').read_text('utf-8'))
    if not isinstance(rows,list):raise ValueError('catalog_list')
    seen=set()
    for row in rows:
        if not isinstance(row,dict) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}',row.get('id','')) or row['id'] in seen:raise ValueError('unique_catalog_id')
        seen.add(row['id'])
        source=contained(root,row.get('file',''))
        if source.suffix.lower() not in {'.png','.jpg','.jpeg','.webp'} or not source.is_file() or source.stat().st_size>20*1024*1024:raise ValueError('bounded_raster_file')
    return rows


def current(state):
    path=Path(state)/'selection.json'
    return json.loads(path.read_text('utf-8')) if path.exists() else {}


def select(root,state,member,identifier,crop):
    if not isinstance(member,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,31}',member):raise ValueError('member_required')
    row=next((r for r in catalog(root) if r['id']==identifier),None)
    if row is None:raise ValueError('catalog_id_required')
    if not isinstance(crop,(list,tuple)) or len(crop)!=3 or any(type(v) not in (int,float) or not math.isfinite(v) or int(v)!=v for v in crop):raise ValueError('integer_square_crop')
    x,y,side=map(int,crop)
    with Image.open(contained(root,row['file'])) as original:
        if original.width*original.height>25_000_000:raise ValueError('bounded_image_dimensions')
        image=ImageOps.exif_transpose(original)
        if not 0<side<=min(image.size) or not 0<=x<=image.width-side or not 0<=y<=image.height-side:raise ValueError('crop_bounds')
        output=io.BytesIO();image.crop((x,y,x+side,y+side)).convert('RGBA').save(output,format='PNG')
    raw=output.getvalue();digest=hashlib.sha256(raw).hexdigest()
    state=Path(state);state.mkdir(parents=True,exist_ok=True)
    name=digest+'.png';target=contained(state,name)
    with storage.locked(state):
        if not target.exists():
            with target.open('xb') as stream:stream.write(raw)
        result=dict(id=identifier,file=name,sha256=digest,crop=[x,y,side])
        value=storage.read(state/'selection.json',{});value[member]=result
        storage.write(state/'selection.json',value)
    return result


def main():
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--catalog',type=Path,required=True)
    parser.add_argument('--state',type=Path);parser.add_argument('--member',choices=['owner','Claude','GPT'])
    parser.add_argument('--select');parser.add_argument('--crop',type=int,nargs=3)
    args=parser.parse_args()
    if args.select:
        if not args.state or not args.member or not args.crop:parser.error('select requires state, member and crop')
        result=select(args.catalog,args.state,args.member,args.select,args.crop)
    else:result=catalog(args.catalog)
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
