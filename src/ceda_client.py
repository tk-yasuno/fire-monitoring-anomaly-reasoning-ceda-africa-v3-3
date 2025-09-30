#!/usr/bin/env python3
"""
CEDA ESA Fire_cci データクライアント
Global Fire Monitoring System v3.2

ESA Fire Climate Change Initiative (Fire_cci): 
MODIS Fire_cci Burned Area Grid product, version 5.1
"""

import os
import sys
import requests
import xarray as xr
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import time
import warnings
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import re
warnings.filterwarnings('ignore')

class CEDAFireCCIClient:
    """CEDA Fire_cci データクライアント"""
    
    def __init__(self, cache_dir="data/ceda_cache"):
        """
        初期化
        
        Args:
            cache_dir (str): キャッシュディレクトリパス
        """
        self.base_url = "https://data.ceda.ac.uk/neodc/esacci/fire/data/burned_area/MODIS/grid/v5.1"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # データ仕様
        self.data_info = {
            "product": "MODIS Fire_cci Burned Area Grid product v5.1",
            "spatial_resolution": "0.25 x 0.25 degrees",
            "temporal_resolution": "Monthly",
            "time_range": "2001-01-01 to 2022-12-31",
            "license": "Open Access",
            "doi": "10.5285/3628cb2fdba443588155e15dee8e5352"
        }
        
        print(f"🔥 CEDA Fire_cci クライアント初期化")
        print(f"📁 キャッシュディレクトリ: {self.cache_dir}")
    
    def get_available_months(self, year=2022):
        """
        利用可能な月データを取得
        
        Args:
            year (int): 年
            
        Returns:
            list: 利用可能な月のリスト
        """
        # 2022年の全月を想定（実際のAPIでは動的に確認）
        if year == 2022:
            return list(range(1, 13))  # 1-12月
        else:
            return []
    
    def build_filename(self, year, month):
        """
        CEDA Fire_cci ファイル名を構築
        
        Args:
            year (int): 年
            month (int): 月
            
        Returns:
            str: ファイル名
        """
        # 実際のファイル名形式は推定
        # 例: 20220101-ESACCI-L4_FIRE-BA-MODIS-fv5.1.nc
        date_str = f"{year:04d}{month:02d}01"
        filename = f"{date_str}-ESACCI-L4_FIRE-BA-MODIS-fv5.1.nc"
        return filename
    
    def build_url(self, year, month):
        """
        ダウンロードURLを構築
        
        Args:
            year (int): 年
            month (int): 月
            
        Returns:
            str: ダウンロードURL
        """
        filename = self.build_filename(year, month)
        url = f"{self.base_url}/{year}/{filename}"
        return url
    
    def get_cache_path(self, year, month):
        """
        キャッシュファイルパスを取得
        
        Args:
            year (int): 年
            month (int): 月
            
        Returns:
            Path: キャッシュファイルパス
        """
        filename = self.build_filename(year, month)
        return self.cache_dir / filename
    
    def download_monthly_data(self, year, month, force_download=False):
        """
        月次データをダウンロード
        
        Args:
            year (int): 年
            month (int): 月
            force_download (bool): 強制ダウンロード
            
        Returns:
            Path: ダウンロードされたファイルパス
        """
        cache_path = self.get_cache_path(year, month)
        
        # キャッシュ確認
        if cache_path.exists() and not force_download:
            print(f"  📦 キャッシュから読み込み: {cache_path.name}")
            return cache_path
        
        # ダウンロード実行
        url = self.build_url(year, month)
        print(f"  🌐 ダウンロード開始: {year}-{month:02d}")
        print(f"     URL: {url}")
        
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # ファイル保存
            with open(cache_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            file_size = cache_path.stat().st_size / (1024 * 1024)  # MB
            print(f"  ✅ ダウンロード完了: {cache_path.name} ({file_size:.1f} MB)")
            return cache_path
            
        except requests.exceptions.RequestException as e:
            print(f"  ❌ ダウンロードエラー: {e}")
            return None
    
    def load_netcdf_data(self, file_path):
        """
        NetCDFファイルを読み込み
        
        Args:
            file_path (Path): ファイルパス
            
        Returns:
            xarray.Dataset: データセット
        """
        try:
            print(f"  📊 NetCDF読み込み: {file_path.name}")
            dataset = xr.open_dataset(file_path)
            
            # データセット情報を表示
            print(f"     座標次元: {list(dataset.coords.keys())}")
            print(f"     データ変数: {list(dataset.data_vars.keys())}")
            
            return dataset
            
        except Exception as e:
            print(f"  ❌ NetCDF読み込みエラー: {e}")
            return None
    
    def create_sample_data(self, year=2022, month=1):
        """
        サンプルデータを生成（実際のCEDAデータが利用できない場合）
        
        Args:
            year (int): 年
            month (int): 月
            
        Returns:
            xarray.Dataset: サンプルデータセット
        """
        print(f"  🎲 サンプルデータ生成: {year}-{month:02d}")
        
        # グリッド定義（0.25度解像度）
        lat = np.arange(-90, 90.25, 0.25)
        lon = np.arange(-180, 180.25, 0.25)
        
        # サンプル焼損面積データ
        burned_area = np.random.exponential(scale=0.1, size=(len(lat), len(lon)))
        burned_area = np.where(burned_area > 1, 0, burned_area)  # 現実的な値に制限
        
        # サンプル信頼度データ
        confidence = np.random.uniform(0.5, 1.0, size=(len(lat), len(lon)))
        
        # 土地被覆クラス（18クラス）
        land_cover = np.random.randint(1, 19, size=(len(lat), len(lon)))
        
        # xarrayデータセット作成
        dataset = xr.Dataset({
            'burned_area': (['lat', 'lon'], burned_area),
            'confidence': (['lat', 'lon'], confidence),
            'land_cover': (['lat', 'lon'], land_cover),
        }, coords={
            'lat': lat,
            'lon': lon,
            'time': pd.Timestamp(f'{year}-{month:02d}-01')
        })
        
        # 属性追加
        dataset.attrs.update({
            'title': 'ESA Fire_cci Burned Area (Sample)',
            'source': 'MODIS Fire_cci v5.1 (Simulated)',
            'spatial_resolution': '0.25 degrees',
            'temporal_resolution': 'Monthly'
        })
        
        return dataset
    
    def get_continental_subset(self, dataset, continent):
        """
        大陸別データサブセットを取得
        
        Args:
            dataset (xarray.Dataset): データセット
            continent (str): 大陸名
            
        Returns:
            xarray.Dataset: 大陸別サブセット
        """
        # 大陸境界定義（v3.1と同じ）
        continent_bounds = {
            'Africa': {'lat_range': (-35, 40), 'lon_range': (-20, 55)},
            'Asia': {'lat_range': (5, 80), 'lon_range': (60, 180)},
            'Europe': {'lat_range': (35, 75), 'lon_range': (-15, 60)},
            'North America': {'lat_range': (15, 85), 'lon_range': (-170, -50)},
            'South America': {'lat_range': (-60, 15), 'lon_range': (-85, -30)}
        }
        
        if continent not in continent_bounds:
            raise ValueError(f"未対応の大陸: {continent}")
        
        bounds = continent_bounds[continent]
        lat_min, lat_max = bounds['lat_range']
        lon_min, lon_max = bounds['lon_range']
        
        # データサブセット
        subset = dataset.sel(
            lat=slice(lat_min, lat_max),
            lon=slice(lon_min, lon_max)
        )
        
        print(f"  🌍 {continent}サブセット: {subset.lat.size}x{subset.lon.size} グリッド")
        return subset
    
    def calculate_statistics(self, dataset):
        """
        データセット統計を計算
        
        Args:
            dataset (xarray.Dataset): データセット
            
        Returns:
            dict: 統計情報
        """
        stats = {}
        
        if 'burned_area' in dataset.data_vars:
            ba = dataset['burned_area']
            stats['total_burned_area'] = float(ba.sum())
            stats['max_burned_area'] = float(ba.max())
            stats['mean_burned_area'] = float(ba.mean())
            stats['active_cells'] = int((ba > 0).sum())
        
        if 'confidence' in dataset.data_vars:
            conf = dataset['confidence']
            stats['mean_confidence'] = float(conf.mean())
            stats['high_confidence_cells'] = int((conf > 0.8).sum())
        
        stats['total_cells'] = int(dataset.lat.size * dataset.lon.size)
        
        return stats

def test_ceda_client():
    """CEDA クライアントテスト"""
    print("🧪 CEDA Fire_cci クライアントテスト")
    print("="*60)
    
    # クライアント初期化
    client = CEDAFireCCIClient()
    
    # 利用可能月取得
    print("\n📅 2022年利用可能月:")
    months = client.get_available_months(2022)
    print(f"  {months}")
    
    # サンプルデータテスト
    print("\n🎲 サンプルデータ生成テスト:")
    sample_data = client.create_sample_data(2022, 1)
    
    print(f"  データ形状: {sample_data.dims}")
    print(f"  変数: {list(sample_data.data_vars.keys())}")
    
    # 大陸別サブセット
    print("\n🌍 大陸別サブセットテスト:")
    continents = ['Africa', 'Asia', 'Europe', 'North America', 'South America']
    
    for continent in continents:
        subset = client.get_continental_subset(sample_data, continent)
        stats = client.calculate_statistics(subset)
        
        print(f"  {continent}:")
        print(f"    総焼損面積: {stats['total_burned_area']:.3f}")
        print(f"    アクティブセル: {stats['active_cells']}")
        print(f"    平均信頼度: {stats['mean_confidence']:.3f}")
    
    print("\n✅ CEDA クライアントテスト完了")

if __name__ == "__main__":
    test_ceda_client()