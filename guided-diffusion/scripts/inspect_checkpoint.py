#!/usr/bin/env python3
"""
Script to inspect a PyTorch checkpoint and determine model architecture parameters
"""

import torch
import argparse
from collections import defaultdict

def inspect_checkpoint(checkpoint_path):
    """Inspect checkpoint to determine model configuration"""
    print(f"Loading checkpoint: {checkpoint_path}")
    
    try:
        # Load checkpoint
        checkpoint = torch.load(checkpoint_path, map_location='cpu')
        
        # Get state dict
        if isinstance(checkpoint, dict) and 'state_dict' in checkpoint:
            state_dict = checkpoint['state_dict']
        else:
            state_dict = checkpoint
            
        print(f"Total parameters in checkpoint: {len(state_dict)}")
        
        # Analyze key patterns
        key_info = defaultdict(list)
        
        for key, tensor in state_dict.items():
            shape = list(tensor.shape)
            key_info[key] = shape
            
        # Determine model dimensions from key patterns
        analysis = {}
        
        # Time embedding dimension
        if 'time_embed.0.weight' in key_info:
            time_embed_dim = key_info['time_embed.0.weight'][0]
            model_channels = key_info['time_embed.0.weight'][1]
            analysis['time_embed_dim'] = time_embed_dim
            analysis['model_channels'] = model_channels
            
        # Input channels
        if 'input_blocks.0.0.weight' in key_info:
            first_conv = key_info['input_blocks.0.0.weight']
            analysis['in_channels'] = first_conv[1]  # Input channels
            analysis['model_channels'] = first_conv[0]  # Model channels
            
        # Output channels
        if 'out.2.weight' in key_info:
            out_conv = key_info['out.2.weight']
            analysis['out_channels'] = out_conv[0]
            
        # Count input and output blocks
        input_blocks = [k for k in key_info.keys() if k.startswith('input_blocks.')]
        output_blocks = [k for k in key_info.keys() if k.startswith('output_blocks.')]
        
        input_block_nums = set()
        output_block_nums = set()
        
        for k in input_blocks:
            parts = k.split('.')
            if len(parts) >= 2:
                input_block_nums.add(int(parts[1]))
                
        for k in output_blocks:
            parts = k.split('.')
            if len(parts) >= 2:
                output_block_nums.add(int(parts[1]))
                
        analysis['num_input_blocks'] = len(input_block_nums)
        analysis['num_output_blocks'] = len(output_block_nums)
        
        # Check for class conditioning
        analysis['class_cond'] = 'label_emb.weight' in key_info
        
        # Check for learned sigma
        if 'out.2.weight' in key_info:
            out_channels = key_info['out.2.weight'][0]
            in_channels = analysis.get('in_channels', 3)
            analysis['learn_sigma'] = out_channels == (in_channels * 2)
            
        # Analyze attention blocks
        attention_keys = [k for k in key_info.keys() if 'qkv.weight' in k]
        analysis['has_attention'] = len(attention_keys) > 0
        
        if attention_keys:
            # Get attention dimensions from first attention block
            first_attn = attention_keys[0]
            qkv_shape = key_info[first_attn]
            channels = qkv_shape[1]
            heads_x3 = qkv_shape[0]
            num_heads = heads_x3 // (3 * channels) * channels
            analysis['attention_example'] = {
                'key': first_attn,
                'qkv_shape': qkv_shape,
                'estimated_heads': num_heads
            }
        
        # Print analysis
        print("\n=== CHECKPOINT ANALYSIS ===")
        for key, value in analysis.items():
            print(f"{key}: {value}")
            
        # Print some example keys and shapes
        print(f"\n=== EXAMPLE KEY SHAPES ===")
        important_keys = [
            'time_embed.0.weight', 'time_embed.2.weight',
            'input_blocks.0.0.weight', 'out.2.weight',
            'label_emb.weight'
        ]
        
        for key in important_keys:
            if key in key_info:
                print(f"{key}: {key_info[key]}")
                
        # Suggest model configuration
        print(f"\n=== SUGGESTED CONFIGURATION ===")
        if 'model_channels' in analysis:
            print(f"--num_channels {analysis['model_channels']}")
        if 'in_channels' in analysis:
            print(f"--in_channels {analysis['in_channels']}")
        if 'out_channels' in analysis:
            print(f"--out_channels {analysis['out_channels']}")
        if analysis.get('class_cond'):
            print("--class_cond True")
        if analysis.get('learn_sigma'):
            print("--learn_sigma True")
            
    except Exception as e:
        print(f"Error loading checkpoint: {e}")
        return None
        
    return analysis

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('checkpoint_path', help='Path to the checkpoint file')
    args = parser.parse_args()
    
    inspect_checkpoint(args.checkpoint_path)

if __name__ == '__main__':
    main()