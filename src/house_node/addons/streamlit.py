import asyncio

import streamlit as st


class NodeFrontend:
  def __init__(self):
    self.run()

  def run(self):
    st.header('Async Streamlit App')
    st.write('This is a simple Streamlit gradio_ui with async support')


if __name__ == '__main__':
  node_frontend = NodeFrontend()
